from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import re
import json
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-to-something-random-later'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

COMMON_PASSWORDS = {"password", "123456", "qwerty", "letmein", "admin", "welcome"}


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)


class Check(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    feedback = db.Column(db.Text, nullable=False)  # stored as JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def score_password(password):
    score = 0
    feedback = []

    if len(password) >= 12:
        score += 25
    elif len(password) >= 9:
        score += 15
    else:
        feedback.append("Use at least 9 characters, ideally 12+")

    if re.search(r'[a-z]', password):
        score += 10
    else:
        feedback.append("Add a lowercase letter.")

    if re.search(r'[A-Z]', password):
        score += 10
    else:
        feedback.append("Add an uppercase letter.")

    if re.search(r'\d', password):
        score += 10
    else:
        feedback.append("Add a number.")

    if re.search(r'[^A-Za-z0-9]', password):
        score += 15
    else:
        feedback.append("Add a special character.")

    if password.lower() in COMMON_PASSWORDS:
        score = min(score, 20)
        feedback.append("This is a commonly used password - avoid it.")

    if re.search(r'(.)\1{2,}', password):
        score -= 10
        feedback.append("Avoid repeated characters (e.g. 'aaa').")

    score = max(0, min(100, score))
    return score, feedback


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/check', methods=['POST'])
def check_password():
    data = request.get_json()
    password = data.get('password', '') if data else ''
    if not password:
        return jsonify({"error": "No password provided"}), 400

    score, feedback = score_password(password)

    if current_user.is_authenticated:
        new_check = Check(
            user_id=current_user.id,
            score=score,
            feedback=json.dumps(feedback)
        )
        db.session.add(new_check)
        db.session.commit()

    return jsonify({"score": score, "feedback": feedback})


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('That username is already taken.')
            return redirect(url_for('register'))

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('home'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))

        flash('Invalid username or password.')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    checks = Check.query.filter_by(user_id=current_user.id).order_by(Check.created_at.desc()).all()
    parsed_checks = [
        {"score": c.score, "feedback": json.loads(c.feedback), "created_at": c.created_at}
        for c in checks
    ]
    return render_template('dashboard.html', checks=parsed_checks)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5002, debug=True)
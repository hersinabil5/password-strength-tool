import os
import re
import json
import hashlib
import requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from zxcvbn import zxcvbn

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-fallback-key-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

csrf = CSRFProtect(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)


class Check(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    feedback = db.Column(db.Text, nullable=False)
    pwned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def check_pwned(password):
    """
    Checks the password against the HaveIBeenPwned breach database
    using the k-anonymity model: only the first 5 characters of the
    SHA-1 hash are sent, never the password or full hash.
    Returns the number of times it's appeared in breaches (0 = not found).
    """
    sha1 = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]

    try:
        response = requests.get(
            f'https://api.pwnedpasswords.com/range/{prefix}',
            timeout=3
        )
        if response.status_code != 200:
            return None  # API unavailable, fail gracefully

        for line in response.text.splitlines():
            hash_suffix, count = line.split(':')
            if hash_suffix == suffix:
                return int(count)
        return 0
    except requests.RequestException:
        return None  # network error, don't block the user


def score_password(password):
    """
    Uses zxcvbn (Dropbox's password strength estimator) instead of
    simple regex rules. zxcvbn models real attacker strategies:
    dictionary words, l33t-speak substitutions, keyboard patterns,
    dates, and common password structures.
    """
    if not password:
        return 0, ["Password cannot be empty."], False

    result = zxcvbn(password)

    # zxcvbn scores 0-4; convert to a 0-100 scale to match your existing frontend
    score = int(result['score'] * 25)

    feedback = []
    warning = result['feedback'].get('warning')
    suggestions = result['feedback'].get('suggestions', [])

    if warning:
        feedback.append(warning)
    feedback.extend(suggestions)

    if not feedback:
        feedback.append("This is a strong password.")

    # Check against real breach data
    pwned_count = check_pwned(password)
    is_pwned = False
    if pwned_count is not None and pwned_count > 0:
        is_pwned = True
        score = min(score, 20)
        feedback.insert(0, f"This password has appeared in {pwned_count:,} known data breaches — do not use it.")

    return score, feedback, is_pwned


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/check', methods=['POST'])
def check_password_route():
    data = request.get_json()
    password = data.get('password', '') if data else ''
    if not password:
        return jsonify({"error": "No password provided"}), 400

    score, feedback, is_pwned = score_password(password)

    if current_user.is_authenticated:
        new_check = Check(
            user_id=current_user.id,
            score=score,
            feedback=json.dumps(feedback),
            pwned=is_pwned
        )
        db.session.add(new_check)
        db.session.commit()

    return jsonify({"score": score, "feedback": feedback, "pwned": is_pwned})


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data

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

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))

        flash('Invalid username or password.')
        return redirect(url_for('login'))

    return render_template('login.html', form=form)


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
        {"score": c.score, "feedback": json.loads(c.feedback), "pwned": c.pwned, "created_at": c.created_at}
        for c in checks
    ]
    return render_template('dashboard.html', checks=parsed_checks)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5002, debug=True)
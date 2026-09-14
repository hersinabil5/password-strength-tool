from flask import Flask, request, jsonify
import re
app = Flask(__name__)

COMMON_PASSWORDS = {"password", "123456", "qwerty", "letmein", "admin", "welcome"}

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
        feedback.append("Add a lowercase letter. ")

    if re.search(r'[A-Z]', password):
        score += 10
    else:
        feedback.append("Add an uppercase letter. ")

    if re.search(r'\d', password):
        score += 10
    else:
        feedback.append("Add a number. ")

    if re.search(r'[^A-Za-z0-9]', password):
        score += 15
    else:
        feedback.append("Add a special character.")

    if password.lower() in COMMON_PASSWORDS:
        score = min(score, 20)
        feedback.append("This is a commonly used password - avoid it.")

    if re.search (r'(.)\1{2,}', password):
        score -= 10
        feedback.append( "Avoid repeated characters (e.g. 'aaa'). ")

    score = max(0, min(100,score))
    return score, feedback


@app.route('/')
def home():
    return "Password Strength Analyzer - use Post /check"

@app.route('/check', methods=['POST'])
def check_password():
    data = request.get_json()
    password = data.get('password','') if data else ''  
    if not password:
        return jsonify({"error": "No password provided"}), 400

    score, feedback = score_password(password)
    return jsonify({
        "score": score,
        "feedback": feedback
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


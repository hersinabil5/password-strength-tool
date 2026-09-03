from flask import Flask, request, jsonify
import re
app = Flask (__name__)

COMMON_PASSWORDS = {"password", "123456", "qwerty", "letmein", "admin", "welcome"}

def score_password(password):
    score = 0
    feedback = []

    if len (password) >=12:
        score +=25
    elif len (password) >= 9:
        score +=15
    else:
        feedback.append("Use at least 9 characters, ideally 12+")

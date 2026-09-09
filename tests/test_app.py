import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import score_password


def test_short_password():
    score, feedback = score_password("abc")
    assert score < 30


def test_long_varied_password():
    score, feedback = score_password("MyStr0ng!Pass")
    assert score >= 70


def test_missing_uppercase():
    score, feedback = score_password("lowercase123!")
    assert "Add an uppercase letter. " in feedback


def test_missing_special_char():
    score, feedback = score_password("Password123")
    assert "Add a special character." in feedback


def test_common_password_capped():
    score, feedback = score_password("password")
    assert score <= 20


def test_repeated_characters_penalized():
    score1, _ = score_password("Abc111!!xyz")
    score2, _ = score_password("Abc123!!xyz")
    assert score1 < score2
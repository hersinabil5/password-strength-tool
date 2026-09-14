import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import score_password


def test_short_password():
    score, feedback, is_pwned = score_password("abc")
    assert score < 30


def test_long_varied_password():
    score, feedback, is_pwned = score_password("Xk9$mQzL2!vRpT")
    assert score >= 50


def test_common_password_flagged_as_pwned():
    score, feedback, is_pwned = score_password("password123")
    assert is_pwned is True
    assert score <= 20


def test_unique_strong_password_not_pwned():
    score, feedback, is_pwned = score_password("Xk9$mQzL2!vRpT")
    assert is_pwned is False


def test_repeated_characters_score_lower():
    score1, _, _ = score_password("Aaa111!!xyzQ")
    score2, _, _ = score_password("Xk93!mQzLpTr")
    assert score1 <= score2


def test_empty_password():
    score, feedback, is_pwned = score_password("")
    assert score == 0
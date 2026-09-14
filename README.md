# Password Strength Analyzer
 
A full-stack web application that evaluates password security using real attacker-modeling techniques and breach data, with user accounts and check history — built as a hands-on project spanning backend development, database design, authentication, security engineering, and DevOps.
 
**Live demo:** [password-strength-tool.onrender.com](https://password-strength-tool.onrender.com)
 
## Features
 
- **Real password strength scoring** using [zxcvbn](https://github.com/dropbox/zxcvbn) (Dropbox's password strength estimator), which models actual attacker guessing strategies — dictionary words, l33t-speak substitutions, keyboard patterns, and common password structures — rather than simple character-type rules.
- **Breach detection** via the [HaveIBeenPwned Pwned Passwords API](https://haveibeenpwned.com/API/v3#PwnedPasswords), using the **k-anonymity model**: only the first 5 characters of a SHA-1 hash are ever sent over the network, so no full password or full hash leaves the server.
- **User accounts** with hashed passwords (Werkzeug's `scrypt`-based hashing — never stored in plain text).
- **Check history** — logged-in users can see a dashboard of their past password checks (score, feedback, breach status, timestamp).
- **Rate-limited login** (5 attempts/minute) to mitigate brute-force attacks.
- **CSRF protection** on all forms.
- **Live-updating frontend** — no page reload needed; scores and feedback update as you type.
## Tech Stack
 
| Layer | Tech |
|---|---|
| Backend | Python 3.13, Flask |
| Auth | Flask-Login, Werkzeug (scrypt password hashing) |
| Database | SQLite, Flask-SQLAlchemy |
| Security | zxcvbn (strength scoring), HaveIBeenPwned API (breach check), Flask-Limiter (rate limiting), Flask-WTF (CSRF) |
| Frontend | Server-rendered HTML/Jinja2, vanilla JS (fetch), CSS |
| Testing | PyTest |
| CI/CD | GitHub Actions |
| Containerization | Docker |
| Deployment | Render |
 
## Architecture
 
```
Browser (JS fetch)
      │
      ▼
Flask app ──► score_password() ──► zxcvbn (strength scoring)
      │                        └──► HaveIBeenPwned API (breach check, k-anonymity)
      │
      ▼
SQLAlchemy ──► SQLite (users, check history)
```
 
## Real Metrics
 
Measured on this project, not estimated.
 
| Metric | Result |
|---|---|
| Test suite | 6/6 passing, 1.19s runtime |
| CI pipeline runtime | ~19s per run (GitHub Actions, `ubuntu-latest`) |
| `/check` endpoint response time (local) | *[measure with the command below]* |
 
To measure the endpoint response time yourself, run the app locally (`python3 app.py`) and in a second terminal:
 
```bash
curl -w "\nTime: %{time_total}s\n" -X POST http://127.0.0.1:5002/check \
  -H "Content-Type: application/json" \
  -d '{"password": "test123"}' -o /dev/null -s
```
 
## Known Limitations
 
- **Breach check depends on an external API.** If HaveIBeenPwned is unreachable, the check fails open (doesn't block the user) rather than blocking password submission — a deliberate availability tradeoff.
- **Rate limiting is in-memory**, not Redis-backed — limits reset on every app restart and won't scale across multiple server instances.
- **SQLite**, not Postgres — fine for a single-instance demo, not concurrent production traffic.
- **`db.create_all()`** instead of real migrations — schema changes currently require manual intervention, not automatic migration.
## Running Locally
 
```bash
git clone https://github.com/hersinabil5/password-strength-tool.git
cd password-strength-tool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
 
Create a `.env` file in the project root:
 
```
SECRET_KEY=your-random-secret-key-here
```
 
(Generate one with: `python3 -c "import secrets; print(secrets.token_hex(16))"`)
 
Then run:
 
```bash
python3 app.py
```
 
Visit `http://127.0.0.1:5002`.
 
## Running with Docker
 
```bash
docker build -t password-tool .
docker run -p 5001:5000 password-tool
```
 
Visit `http://127.0.0.1:5001`.
 
## Running Tests
 
```bash
pytest
```
 
Tests cover password scoring behavior (including empty-input edge cases) and breach detection against the real HaveIBeenPwned API.
 
## Security Notes
 
- Passwords are never stored — only Werkzeug-generated hashes.
- Only 5 hex characters of a password's SHA-1 hash are ever transmitted for breach checking (k-anonymity).
- `SECRET_KEY` is loaded from an environment variable, never hardcoded or committed.
- Login endpoint is rate-limited to reduce brute-force risk.
## Future Improvements
 
- PostgreSQL instead of SQLite for production-grade concurrency
- Database migrations via Flask-Migrate/Alembic
- Redis-backed rate limiting (currently in-memory, resets on restart)
- Security headers (CSP, HSTS) via Flask-Talisman
- OpenAPI/Swagger documentation for the `/check` API
## What I Learned
 
This project took me from a simple regex-based scoring script to a deployed, tested, security-conscious full-stack application. Along the way I worked through real debugging scenarios — Docker networking issues, indentation errors, port conflicts, CI failures from a changed function signature — that reflect the kind of troubleshooting real development work involves.
 
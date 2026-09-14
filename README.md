# Password Strength Tool

A small Flask API that scores password strength (0-100) and returns actionable
feedback for improving weak passwords.

## Scoring

A password earns points for:

- **Length** — 25 points for 12+ characters, 15 points for 9-11 characters
- **Character variety** — 10 points each for lowercase, uppercase, and digits;
  15 points for a special character
- Points are capped at 20 if the password is a known common password
  (e.g. `password`, `123456`, `qwerty`)
- 10 points are deducted for repeated-character runs (e.g. `aaa`)

The final score is clamped to the range 0-100.

## Running locally

```bash
pip install -r requirements.txt
python app.py
```

The API listens on `http://localhost:5000`.

## Running with Docker

```bash
docker build -t password-strength-tool .
docker run -p 5000:5000 password-strength-tool
```

## API

### `POST /check`

Request body:

```json
{ "password": "Abc123!!" }
```

Response:

```json
{
  "score": 45,
  "feedback": ["Use at least 9 characters, ideally 12+"]
}
```

Example:

```bash
curl -X POST http://localhost:5000/check \
  -H "Content-Type: application/json" \
  -d '{"password": "Abc123!!"}'
```

## Tests

```bash
pytest
```

Tests run automatically on push and pull request via GitHub Actions
(see `.github/workflows/test.yml`).

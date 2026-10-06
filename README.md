# JAYKAY API

A study assistant backend for students who dislike long reading. Users paste text or upload a file (PDF, PPTX, TXT, MD), and the API uses Claude to turn it into:

- a short, plain-language **summary**
- **flashcards** (8-15)
- a multiple-choice **quiz** (5-10 questions, 4 options each, with explanations)

Built with **FastAPI**, **SQLAlchemy** and **MySQL**. Payments for Premium are handled with manual mobile money approval by an admin.

---

## Features

- Email + password accounts with JWT authentication
- Login rate limiting (per email + IP)
- Free and Premium plans with different daily limits and text-length limits
- File upload with text extraction (PDF, PPTX, TXT, MD), max 5 MB
- AI generation guarded against prompt injection (material is treated as data only)
- Manual Premium upgrade flow: user requests, admin approves or rejects
- Admin endpoints for users and payments
- Users can only ever access their own study sets
- Security headers and a strict CORS allow-list

---

## Project structure

```
app/
├── __init__.py
├── main.py           # FastAPI app, CORS, security headers, startup (creates tables + admin)
├── config.py         # Settings loaded from environment / .env
├── db.py             # SQLAlchemy engine, session, Base
├── models.py         # User, StudySet, Payment
├── schemas.py        # Pydantic request models and validation
├── security.py       # Password hashing, JWT, auth dependencies, login throttling
├── ai.py             # Claude call + response validation
├── routes_auth.py    # /auth: register, login, me
├── routes_study.py   # /study: generate, upload, list, get, delete
├── routes_pay.py     # /payments: request upgrade, list my payments
└── routes_admin.py   # /admin: settings, users, payments, approve, reject
```

> `security.py` is imported by the app but is not included in the files listed here. Make sure it exists in your package.

---

## Requirements

- Python 3.10+
- MySQL 8 (or compatible)
- An Anthropic API key

Python packages (based on the imports in the code):

```
fastapi
uvicorn
sqlalchemy
pymysql
pydantic-settings
pydantic[email]
python-multipart
anthropic
pypdf
python-pptx
```

Plus whatever `security.py` uses for password hashing and JWT (for example `bcrypt` and `pyjwt`).

---

## Setup

1. **Create the database**

   ```sql
   CREATE DATABASE jaykay CHARACTER SET utf8mb4;
   CREATE USER 'jaykay'@'localhost' IDENTIFIED BY 'jaykay_pass';
   GRANT ALL PRIVILEGES ON jaykay.* TO 'jaykay'@'localhost';
   ```

2. **Install dependencies**

   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install fastapi uvicorn sqlalchemy pymysql pydantic-settings "pydantic[email]" \
               python-multipart anthropic pypdf python-pptx
   ```

3. **Create a `.env` file** (see below)

4. **Run the server** from the folder that contains the package:

   ```bash
   uvicorn app.main:app --reload
   ```

   Replace `app` with your actual package folder name. Because the code uses relative imports, it must be run as a package, not as `python main.py`.

5. Open the interactive docs at **http://localhost:8000/docs**

On first startup the app creates all tables and an admin account from `ADMIN_EMAIL` and `ADMIN_PASSWORD`.

---

## Configuration

All settings come from environment variables or a `.env` file.

```env
DATABASE_URL=mysql+pymysql://jaykay:jaykay_pass@localhost:3306/jaykay
JWT_SECRET=put-a-long-random-string-here
ANTHROPIC_API_KEY=sk-ant-...
AI_MODEL=claude-sonnet-5-5

ADMIN_EMAIL=admin@jaykay.local
ADMIN_PASSWORD=choose-a-strong-password
OWNER_PAYMENT_NUMBER=07XXXXXXXX

CORS_ORIGINS=http://localhost:5173
```

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | local MySQL | SQLAlchemy connection string |
| `JWT_SECRET` | `change-me` | Secret used to sign tokens. **Change it.** |
| `JWT_EXPIRE_MINUTES` | 1440 (24h) | Token lifetime |
| `ANTHROPIC_API_KEY` | empty | Required for generation; without it the API returns 503 |
| `AI_MODEL` | `claude-sonnet-5-5` | Claude model used |
| `ADMIN_EMAIL` | `admin@jaykay.local` | Admin account created on first start |
| `ADMIN_PASSWORD` | `change-this-now` | **Change it.** |
| `OWNER_PAYMENT_NUMBER` | empty | Your receiving number; only ever returned to admins |
| `PREMIUM_PRICE` | 10000 | Price per period |
| `CURRENCY` | `UGX` | Currency label |
| `PREMIUM_DAYS` | 30 | Days of Premium per approved payment |
| `FREE_DAILY_LIMIT` | 3 | Study sets per day (free) |
| `PREMIUM_DAILY_LIMIT` | 50 | Study sets per day (premium) |
| `FREE_MAX_CHARS` | 6000 | Max input length (free) |
| `PREMIUM_MAX_CHARS` | 60000 | Max input length (premium) |
| `MAX_UPLOAD_BYTES` | 5 MB | Max upload size |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed origins |

---

## API overview

Authenticated routes need the header `Authorization: Bearer <token>`.

### Auth

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create an account (password 8-72 chars). Returns token + user |
| POST | `/auth/login` | Log in. Returns token + user |
| GET | `/auth/me` | Current user, plan, daily usage and limits |

### Study

| Method | Path | Description |
|---|---|---|
| POST | `/study/generate` | Body: `{ "title": "...", "text": "..." }` (min 50 chars) |
| POST | `/study/upload` | Multipart form: `title` + `file` (PDF, PPTX, TXT, MD) |
| GET | `/study` | List your study sets |
| GET | `/study/{id}` | Get one set with summary, flashcards, quiz |
| DELETE | `/study/{id}` | Delete one of your sets |

Possible errors: `429` daily limit reached, `413` text too long for your plan or file too large, `400` unreadable/unsupported file, `502` AI failure, `503` AI not configured.

### Payments

| Method | Path | Description |
|---|---|---|
| POST | `/payments/request` | Body: `{ "payer_phone": "0770000000" }`. Creates a pending upgrade request |
| GET | `/payments/mine` | Your payment requests and their status |

Phone numbers must be Ugandan mobile numbers (`07XXXXXXXX` or `+2567XXXXXXXX`). Only one pending request per user is allowed.

### Admin (admin role only)

| Method | Path | Description |
|---|---|---|
| GET | `/admin/settings` | Returns the owner payment number |
| GET | `/admin/users` | Latest 500 users |
| GET | `/admin/payments` | Latest 500 payments |
| POST | `/admin/payments/{id}/approve` | Approve and grant Premium (extends if already active) |
| POST | `/admin/payments/{id}/reject` | Reject a pending request |

### Other

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |

---

## How Premium works

1. The user calls `POST /payments/request` with their own mobile money number.
2. A pending payment with a unique reference (e.g. `JK-AB12CD34EF`) is created.
3. The admin sees it in `/admin/payments`, sends a mobile money request to the user, and confirms payment.
4. The admin calls `approve`. The user becomes Premium for `PREMIUM_DAYS` days (added on top of any remaining time).

`routes_pay.py` is the place to plug in an automatic provider such as MTN MoMo or Flutterwave later.

---

## Security notes

- Change `JWT_SECRET`, `ADMIN_PASSWORD` and the default database password before deploying.
- The owner payment number is returned only by `/admin/settings`, never to normal users.
- Study material is wrapped in `<material>` tags and the model is told to treat it as data, not instructions.
- AI output is parsed and validated before it is saved; malformed quiz questions are dropped.
- CORS only allows the origins in `CORS_ORIGINS`, with `GET`, `POST`, `DELETE`.
- Responses include `X-Content-Type-Options`, `X-Frame-Options` and `Referrer-Policy` headers.
- Run behind HTTPS in production.

---

## Notes and ideas for later

- Tables are created automatically with `create_all`; consider Alembic migrations as the schema grows.
- Login throttling lives in `security.py`; if it is in-memory, it resets on restart and does not share across multiple workers. Use Redis for multi-worker deployments.
- Automate Premium with a mobile money API instead of manual approval.

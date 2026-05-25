# cloudbox_backend

FastAPI backend for CloudBox — multi-cloud VPS provisioning (Contabo API, JWT auth, user-scoped servers).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with Contabo API credentials and JWT_SECRET
./run.sh
```

API docs: http://127.0.0.1:8000/docs

## Environment

See `.env.example` for required variables (`CONTABO_*`, `JWT_SECRET`, `DATABASE_URL`).

## Test Contabo credentials

```bash
PYTHONPATH=. python scripts/test_contabo_auth.py
```

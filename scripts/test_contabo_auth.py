#!/usr/bin/env python3
"""Test Contabo OAuth credentials from backend/.env

Run from backend/:
  PYTHONPATH=. python scripts/test_contabo_auth.py
"""

import asyncio
import sys
from pathlib import Path

# Allow running as script from backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from app.config import get_settings


async def main() -> int:
    s = get_settings()
    if not s.contabo_configured():
        print("Missing CONTABO_* variables in .env")
        return 1

    print(f"Client ID: {s.contabo_client_id[:8]}...")
    print(f"API User:  {s.contabo_api_user}")
    print("Testing token request...")

    data = {
        "client_id": s.contabo_client_id,
        "client_secret": s.contabo_client_secret,
        "username": s.contabo_api_user,
        "password": s.contabo_api_password,
        "grant_type": "password",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(s.contabo_auth_url, data=data)

    if response.status_code == 200 and response.json().get("access_token"):
        print("OK — access token received.")
        return 0

    print(f"FAILED ({response.status_code}): {response.text}")
    if response.status_code == 401:
        print(
            "\nFix: https://my.contabo.com/account/api\n"
            "  1. Confirm API User email matches CONTABO_API_USER\n"
            "  2. Click to set/reset API Password (separate from login password)\n"
            "  3. Update CONTABO_API_PASSWORD in .env and restart uvicorn"
        )
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE = "https://questions.aloc.com.ng"
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
TOKEN = os.getenv("API_KEY_1")
HEADERS = {"Accept": "application/json", "AccessToken": TOKEN}

def req(label, url, method="GET", data=None, headers=None):
    try:
        r = requests.request(method, url, json=data, headers=headers or HEADERS, timeout=10)
        print(f"\n[{label}]")
        print(f"  status : {r.status_code}")
        print(f"  snippet: {r.text[:300]}")
        return r
    except requests.exceptions.Timeout:
        print(f"\n[{label}] TIMEOUT")
        return None
    except Exception as e:
        print(f"\n[{label}] ERROR: {e}")
        return None

print("\n=== 1. FIND LOGIN ENDPOINT ===")
login_endpoints = [
    "/api/v2/login", "/api/v2/auth/login", "/api/v2/auth",
    "/api/login", "/api/auth", "/api/v2/user/login",
    "/api/v2/signin", "/api/v2/auth/signin",
    "/login", "/signin", "/auth/login",
]
for ep in login_endpoints:
    req(ep, BASE + ep, method="POST", data={"email": EMAIL, "password": PASSWORD})

print("\n=== 2. TRY LOGIN WITH JSON ===")
req("POST json login", f"{BASE}/api/v2/login",
    method="POST",
    data={"email": EMAIL, "password": PASSWORD},
    headers={"Accept": "application/json", "Content-Type": "application/json"})

print("\n=== 3. TRY LOGIN WITH FORM DATA ===")
try:
    r = requests.post(f"{BASE}/api/v2/login",
                      data={"email": EMAIL, "password": PASSWORD},
                      headers={"Accept": "application/json"}, timeout=10)
    print(f"\n[form login] {r.status_code}: {r.text[:300]}")
except Exception as e:
    print(f"\n[form login] ERROR: {e}")

print("\n=== 4. CHECK IF TOKEN BELONGS TO ACCOUNT ===")
account_endpoints = [
    "/api/v2/me", "/api/v2/user", "/api/v2/profile",
    "/api/v2/account", "/api/v2/user/me",
]
for ep in account_endpoints:
    req(ep, BASE + ep)

print("\nDone.")

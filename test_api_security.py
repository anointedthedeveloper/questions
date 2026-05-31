import requests
import json

TOKEN = "QB-f8fd0811d3a19d9bc3ac"
BASE = "https://questions.aloc.com.ng"
HEADERS = {"Accept": "application/json", "AccessToken": TOKEN}

results = {}

def test(name, url, headers=HEADERS):
    try:
        r = requests.get(url, headers=headers, timeout=10)
        results[name] = {"status": r.status_code, "snippet": r.text[:200]}
        print(f"\n[{name}]")
        print(f"  status : {r.status_code}")
        print(f"  snippet: {r.text[:200]}")
        return r
    except requests.exceptions.Timeout:
        results[name] = {"status": "TIMEOUT", "snippet": ""}
        print(f"\n[{name}]")
        print(f"  status : TIMEOUT — server hung on this request (potential DoS vector)")
        return None
    except Exception as e:
        results[name] = {"status": "ERROR", "snippet": str(e)}
        print(f"\n[{name}] ERROR: {e}")
        return None

# 1. No auth
test("no_auth", f"{BASE}/api/v2/q/5?subject=mathematics", headers={"Accept": "application/json"})

# 2. SQL injection in subject
test("sql_injection", f"{BASE}/api/v2/q/5?subject=mathematics' OR '1'='1")

# 3. Path traversal
test("path_traversal", f"{BASE}/api/v2/q/5?subject=../../../etc/passwd")

# 4. Exposed .env
test("env_file", f"{BASE}/.env", headers={"Accept": "*/*"})

# 5. Exposed phpinfo
test("phpinfo", f"{BASE}/phpinfo.php", headers={"Accept": "*/*"})

# 6. Large count — can we pull more than 5?
r = test("large_count", f"{BASE}/api/v2/q/100?subject=mathematics")
if r:
    try:
        count = len(r.json().get("data", []))
        print(f"  >> returned {count} questions")
    except: pass

# 7. Year + type filter — enumerate specific years
test("year_filter_2020", f"{BASE}/api/v2/q/5?subject=mathematics&type=utme&year=2020")

# 8. CORS — any origin allowed?
try:
    r = requests.get(f"{BASE}/api/v2/q/5?subject=mathematics", headers={**HEADERS, "Origin": "https://evil.com"}, timeout=10)
    cors = r.headers.get("Access-Control-Allow-Origin", "not set")
except:
    cors = "ERROR"
print(f"\n[cors_check]")
print(f"  Access-Control-Allow-Origin: {cors}")
results["cors"] = cors

# 9. Server info leak
try:
    r = requests.get(f"{BASE}/api/v2/q/5?subject=mathematics", headers=HEADERS, timeout=10)
    server = r.headers.get("Server", "not set")
except:
    server = "ERROR"
print(f"\n[server_header]")
print(f"  Server: {server}")
results["server_header"] = server

# 10. Token reuse from different fake user-agent (no binding check)
try:
    r = requests.get(f"{BASE}/api/v2/q/5?subject=mathematics",
                     headers={**HEADERS, "User-Agent": "EvilBot/1.0"}, timeout=10)
    print(f"\n[token_binding_check]")
    print(f"  status with fake user-agent: {r.status_code} — token has NO binding" if r.status_code == 200 else f"  blocked: {r.status_code}")
except Exception as e:
    print(f"\n[token_binding_check] ERROR: {e}")

# Summary
print("\n" + "="*50)
print("SUMMARY")
print("="*50)
checks = {
    "Auth required":          results.get("no_auth", {}).get("status") not in [200],
    "SQL injection blocked":  results.get("sql_injection", {}).get("status") == 406,
    "Path traversal blocked": results.get("path_traversal", {}).get("status") == 406,
    ".env not exposed":       results.get("env_file", {}).get("status") != 200,
    "phpinfo not exposed":    results.get("phpinfo", {}).get("status") != 200,
    "CORS restricted":        results.get("cors") != "*",
    "Server header hidden":   "Apache" not in str(results.get("server_header", "")),
    "Large count not hanging": results.get("large_count", {}).get("status") != "TIMEOUT",
}
for check, passed in checks.items():
    print(f"  {'PASS' if passed else 'FAIL'}  {check}")

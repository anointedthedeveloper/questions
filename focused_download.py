import requests
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import dotenv_values

BASE_URL = "https://questions.aloc.com.ng/api/v2/q/5"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_env = dotenv_values(os.path.join(SCRIPT_DIR, ".env"))
API_KEYS = [v for k, v in sorted(_env.items()) if k.startswith("API_KEY_")]
HEADERS_LIST = [{"Accept": "application/json", "AccessToken": k} for k in API_KEYS]

OUTPUT_DIR = os.path.join(SCRIPT_DIR, "questions")
NO_NEW_LIMIT = 3
REQUESTS_PER_ROUND = max(1, min(30, len(API_KEYS) // 8))

RATE_LIMIT = 58
key_lock = __import__('threading').Lock()
current_key = 0
key_counts = [0] * len(API_KEYS)
key_reset = [time.time()] * len(API_KEYS)


def pick_key():
    global current_key
    with key_lock:
        now = time.time()
        for i in range(len(API_KEYS)):
            if now - key_reset[i] >= 60:
                key_counts[i] = 0
                key_reset[i] = now
        for i in range(len(API_KEYS)):
            idx = (current_key + i) % len(API_KEYS)
            if key_counts[idx] < RATE_LIMIT:
                key_counts[idx] += 1
                current_key = (idx + 1) % len(API_KEYS)
                return HEADERS_LIST[idx]
        wait = 60 - (time.time() - min(key_reset))
        time.sleep(max(wait, 1))
        for i in range(len(API_KEYS)):
            key_counts[i] = 0
            key_reset[i] = time.time()
        key_counts[0] += 1
        return HEADERS_LIST[0]


INCOMPLETE = [
    "government", "commerce",
    "accounting", "civiledu", "crk", "insurance"
]


def single_request(subject):
    try:
        r = requests.get(BASE_URL, headers=pick_key(), params={"subject": subject}, timeout=(10, 30))
        if r.status_code == 200:
            data = r.json().get("data", [])
            if isinstance(data, dict):
                data = [data]
            return [q for q in data if q.get("id") and q.get("question")]
    except:
        pass
    return []


def fetch_parallel(subject):
    merged = {}
    with ThreadPoolExecutor(max_workers=REQUESTS_PER_ROUND) as ex:
        futures = [ex.submit(single_request, subject) for _ in range(REQUESTS_PER_ROUND)]
        for f in as_completed(futures):
            for q in f.result():
                merged[q["id"]] = q
    return list(merged.values())


def load_subject(subject):
    path = os.path.join(OUTPUT_DIR, f"{subject}.json")
    if not os.path.exists(path):
        return {}, set()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        seen = {q["id"]: q for q in data if q.get("id")}
        return seen, set(seen.keys())
    except:
        return {}, set()


def save_subject(subject, seen_dict):
    path = os.path.join(OUTPUT_DIR, f"{subject}.json")
    tmp = path + f".{os.getpid()}.tmp"
    merged = sorted(seen_dict.values(), key=lambda q: int(q.get("id", 0)))
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def verify(subject, seen_ids):
    for _ in range(5):
        data = fetch_parallel(subject)
        new = [q for q in data if q["id"] not in seen_ids]
        if new:
            return True, len(new)
    return False, 0


def download_subject(subject):
    print(f"\n{'='*50}")
    print(f"[{subject}] starting download")
    seen_dict, seen_ids = load_subject(subject)
    total = len(seen_dict)
    print(f"[{subject}] {total} questions already saved")

    no_new_streak = 0
    round_num = 0

    while no_new_streak < NO_NEW_LIMIT:
        round_num += 1
        t0 = time.time()
        data = fetch_parallel(subject)
        elapsed = time.time() - t0
        new = [q for q in data if q["id"] not in seen_ids]

        if new:
            for q in new:
                seen_ids.add(q["id"])
                seen_dict[q["id"]] = q
            total += len(new)
            no_new_streak = 0
            save_subject(subject, seen_dict)
            print(f"[{subject}] round {round_num}: +{len(new)} (total {total}) [{elapsed:.1f}s]")
        else:
            no_new_streak += 1
            print(f"[{subject}] round {round_num}: no new ({no_new_streak}/{NO_NEW_LIMIT}) [{elapsed:.1f}s]")

    print(f"[{subject}] download finished: {total} questions")

    print(f"[{subject}] verifying...")
    has_more, count = verify(subject, seen_ids)
    if has_more:
        print(f"[{subject}] WARNING: API still returning {count} new questions — may need another pass")
        return False, total
    else:
        print(f"[{subject}] VERIFIED complete: {total} questions")
        return True, total


# --- Main ---
os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"Loaded {len(API_KEYS)} API keys | {REQUESTS_PER_ROUND} parallel requests/round per subject")
print(f"Subjects to download: {INCOMPLETE}\n")

results = {}
for subject in INCOMPLETE:
    done, total = download_subject(subject)
    results[subject] = {"done": done, "total": total}

print(f"\n{'='*50}")
print("FINAL RESULTS:")
for subject, info in results.items():
    status = "COMPLETE" if info["done"] else "NEEDS ANOTHER PASS"
    print(f"  {subject:<25} {info['total']:>6} questions  [{status}]")

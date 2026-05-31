import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_KEYS = [os.getenv("API_KEY_1"), os.getenv("API_KEY_2")]
BASE = "https://questions.aloc.com.ng"
BATCH = 10          # /api/v2/m/10 — 50 times out, 10 is stable (2x faster than /q/5)
DELAY = 1.0         # seconds between requests
OUTPUT_DIR = "../questions"
PROGRESS_FILE = "progress_fast.json"

SUBJECTS = [
    "english", "mathematics", "commerce", "accounting", "biology",
    "physics", "chemistry", "englishlit", "government", "crk",
    "geography", "economics", "irk", "civiledu", "insurance",
    "currentaffairs", "history"
]

key_index = 0
key_counts = [0, 0]
key_resets = [time.time(), time.time()]

def headers():
    return {"Accept": "application/json", "AccessToken": API_KEYS[key_index]}

def rotate():
    global key_index
    key_index = (key_index + 1) % len(API_KEYS)
    print(f"  [key rotated -> key {key_index + 1}]")

def get_total(subject):
    try:
        r = requests.get(f"{BASE}/api/metrics/questions-available-for/{subject}",
                         headers=headers(), timeout=10)
        return r.json().get("data", {}).get("questions", 0)
    except:
        return 0

def fetch_batch(subject, retries=3):
    global key_index, key_counts, key_resets
    for attempt in range(retries):
        now = time.time()
        if now - key_resets[key_index] >= 60:
            key_counts[key_index] = 0
            key_resets[key_index] = now
        if key_counts[key_index] >= 58:
            other = (key_index + 1) % 2
            if now - key_resets[other] >= 60:
                key_counts[other] = 0
                key_resets[other] = now
            if key_counts[other] < 58:
                rotate()
            else:
                wait = 60 - (now - key_resets[key_index])
                print(f"  both keys limited, waiting {wait:.0f}s...")
                time.sleep(max(wait, 1))
                key_counts[key_index] = 0
                key_resets[key_index] = time.time()
        try:
            r = requests.get(f"{BASE}/api/v2/m/{BATCH}",
                             headers=headers(),
                             params={"subject": subject},
                             timeout=15)
            key_counts[key_index] += 1
            if r.status_code == 429:
                key_counts[key_index] = 60
                rotate()
                continue
            if r.status_code == 200:
                return r.json().get("data", [])
        except Exception as e:
            print(f"  attempt {attempt+1} failed: {e}")
            time.sleep(3)
    return []

def fetch_by_id(subject, qid):
    try:
        r = requests.get(f"{BASE}/api/v2/q-by-id/{qid}",
                         headers=headers(),
                         params={"subject": subject},
                         timeout=10)
        key_counts[key_index] += 1
        if r.status_code == 200:
            data = r.json().get("data")
            if data and isinstance(data, dict):
                return data
    except:
        pass
    return None

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}

def save_progress(p):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(p, f, indent=2)

def load_ids(subject):
    path = os.path.join(OUTPUT_DIR, f"{subject}.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return {q["id"] for q in json.load(f)}
    return set()

def save_questions(subject, questions):
    path = os.path.join(OUTPUT_DIR, f"{subject}.json")
    existing = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            existing = json.load(f)
    existing.extend(questions)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

os.makedirs(OUTPUT_DIR, exist_ok=True)
progress = load_progress()

for subject in SUBJECTS:
    sp = progress.get(subject, {"done": False, "total": 0})
    if sp.get("done"):
        print(f"\n[{subject}] already done ({sp['total']} questions), skipping")
        continue

    total_available = get_total(subject)
    print(f"\n[{subject}] total available: {total_available}")
    time.sleep(0.5)

    seen_ids = load_ids(subject)
    saved = len(seen_ids)
    if saved > 0:
        print(f"  resuming — {saved} already saved")

    no_new_streak = 0
    round_num = 0
    MAX_DRY = 10

    while True:
        round_num += 1
        batch = fetch_batch(subject)
        new = [q for q in batch if isinstance(q, dict) and q.get("id") and q["id"] not in seen_ids]

        if new:
            for q in new:
                seen_ids.add(q["id"])
            saved += len(new)
            no_new_streak = 0
            save_questions(subject, new)
            print(f"  round {round_num}: +{len(new)} new (total {saved}/{total_available})")
        else:
            no_new_streak += 1
            print(f"  round {round_num}: no new ({no_new_streak}/{MAX_DRY})")
            if no_new_streak >= MAX_DRY:
                print(f"  exhausted after {MAX_DRY} dry rounds")
                break

        if total_available and saved >= total_available:
            print(f"  reached total {total_available}, done!")
            break

        progress[subject] = {"done": False, "total": saved}
        save_progress(progress)
        time.sleep(DELAY)

    progress[subject] = {"done": True, "total": saved}
    save_progress(progress)
    print(f"  [{subject}] complete: {saved} questions")

print("\nAll done!")

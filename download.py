import requests
import json
import os
import time
import threading
import socket
import ctypes
from dotenv import dotenv_values

ES_CONTINUOUS        = 0x80000000
ES_SYSTEM_REQUIRED   = 0x00000001
ES_DISPLAY_REQUIRED  = 0x00000002

def prevent_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )

def allow_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

def prevent_shutdown():
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    ctypes.windll.user32.ShutdownBlockReasonCreate(hwnd, "Download in progress")

def allow_shutdown():
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    ctypes.windll.user32.ShutdownBlockReasonDestroy(hwnd)

# Load all API_KEY_* from .env dynamically
_env = dotenv_values(".env")
API_KEYS = [v for k, v in sorted(_env.items()) if k.startswith("API_KEY_")]
if not API_KEYS:
    # fallback to hardcoded keys if .env has none
    API_KEYS = [
        "QB-f8fd0811d3a19d9bc3ac",
        "ALOC-eb5ef0a13fdb416ad27a",
        "ALOC-3ac4f2f1f2f83eb6c0d7",
        "QB-d50f30a40f9b835a11ba",
    ]
print(f"[config] loaded {len(API_KEYS)} API keys")

MACHINE_ID = socket.gethostname()
LOCK_FILE = "subject_locks.json"
LOCK_TIMEOUT = 30 * 60
BASE_URL = "https://questions.aloc.com.ng/api/v2/q/5"
HEADERS_LIST = [
    {"Accept": "application/json", "AccessToken": k} for k in API_KEYS
]

SUBJECTS = [
    "mathematics", "english", "chemistry", "physics", "biology",
    "economics", "government", "englishlit", "geography",
    "commerce", "accounting", "civiledu", "agricultural-science",
    "crk", "irk",
    "further-mathematics", "computer-studies", "home-economics",
    "yoruba", "igbo", "hausa", "currentaffairs", "history", "insurance"
]

OUTPUT_DIR = "questions"
PROGRESS_FILE = "progress.json"
MAX_ROUNDS = 200
NO_NEW_LIMIT = 15
RATE_LIMIT = 58  # per key per minute
# With 100 keys: 5800 req/min capacity vs 24 subjects — delay is negligible
DELAY = max(60 / (RATE_LIMIT * len(API_KEYS)), 0.05)  # floor at 50ms to be polite

# One worker per subject — all subjects run in parallel
WORKERS = len(SUBJECTS)

key_lock = threading.Lock()
file_lock_mutex = threading.Lock()
current_key = 0
key_counts = [0] * len(API_KEYS)
key_reset = [time.time()] * len(API_KEYS)
progress_lock = threading.Lock()
file_locks = {}


def get_file_lock(subject):
    if subject not in file_locks:
        file_locks[subject] = threading.Lock()
    return file_locks[subject]


def smart_request(subject):
    global current_key

    for attempt in range(3):
        with key_lock:
            now = time.time()
            # reset expired windows
            for i in range(len(API_KEYS)):
                if now - key_reset[i] >= 60:
                    key_counts[i] = 0
                    key_reset[i] = now

            # pick key with lowest count under limit
            chosen = None
            for i in range(len(API_KEYS)):
                idx = (current_key + i) % len(API_KEYS)
                if key_counts[idx] < RATE_LIMIT:
                    chosen = idx
                    break

            if chosen is None:
                wait = 60 - (time.time() - min(key_reset))
                print(f"  [all keys limited, waiting {wait:.0f}s]")
                time.sleep(max(wait, 1))
                for i in range(len(API_KEYS)):
                    key_counts[i] = 0
                    key_reset[i] = time.time()
                chosen = 0

            key_counts[chosen] += 1
            current_key = (chosen + 1) % len(API_KEYS)
            headers = HEADERS_LIST[chosen]

        try:
            r = requests.get(BASE_URL, headers=headers,
                             params={"subject": subject}, timeout=20)

            if r.status_code == 429:
                with key_lock:
                    key_counts[chosen] = RATE_LIMIT
                continue

            if r.status_code == 200:
                data = r.json().get("data", [])
                if isinstance(data, dict):
                    data = [data]
                return [q for q in data if q.get("id") and q.get("question")]

        except Exception as e:
            print(f"  [{subject}] attempt {attempt+1} failed: {e}")
            time.sleep(3)

    return []


def load_locks():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE) as f:
                content = f.read().strip()
                if not content:
                    return {"locks": {}}
                return json.loads(content)
        except (json.JSONDecodeError, Exception):
            return {"locks": {}}
    return {"locks": {}}

def save_locks(locks):
    with open(LOCK_FILE, "w") as f:
        json.dump(locks, f, indent=2)

def claim_subject(subject):
    with file_lock_mutex:
        data = load_locks()
        locks = data.get("locks", {})
        now = time.time()
        if subject in locks:
            owner = locks[subject]["machine"]
            claimed_at = locks[subject]["time"]
            if owner != MACHINE_ID and now - claimed_at < LOCK_TIMEOUT:
                print(f"  [{subject}] claimed by {owner}, skipping")
                return False
        locks[subject] = {"machine": MACHINE_ID, "time": now}
        data["locks"] = locks
        save_locks(data)
        return True

def release_subject(subject):
    with file_lock_mutex:
        data = load_locks()
        locks = data.get("locks", {})
        if subject in locks and locks[subject]["machine"] == MACHINE_ID:
            del locks[subject]
            data["locks"] = locks
            save_locks(data)

def renew_lock(subject):
    with file_lock_mutex:
        data = load_locks()
        locks = data.get("locks", {})
        if subject in locks and locks[subject]["machine"] == MACHINE_ID:
            locks[subject]["time"] = time.time()
            data["locks"] = locks
            save_locks(data)


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}


def save_progress(progress):
    with progress_lock:
        with open(PROGRESS_FILE, "w") as f:
            json.dump(progress, f, indent=2)


def verify_and_load(subject):
    """Fast verify: load file, check valid JSON, return (questions, seen_ids)."""
    filepath = os.path.join(OUTPUT_DIR, f"{subject}.json")
    if not os.path.exists(filepath):
        return [], set()

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # filter out any blank/corrupt entries
        valid = [q for q in data if q.get("id") and q.get("question", "").strip()]
        removed = len(data) - len(valid)

        if removed > 0:
            print(f"  [verify] removed {removed} blank/corrupt entries")
            # rewrite clean file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(valid, f, ensure_ascii=False, indent=2)

        seen = {q["id"] for q in valid}
        print(f"  [verify] {len(valid)} valid questions loaded (ids: {min(seen)} - {max(seen)})")
        return valid, seen

    except (json.JSONDecodeError, Exception) as e:
        print(f"  [verify] file corrupt: {e} — starting fresh")
        os.rename(filepath, filepath + ".corrupt")
        return [], set()


def append_questions(subject, new_questions):
    filepath = os.path.join(OUTPUT_DIR, f"{subject}.json")
    with get_file_lock(subject):
        existing = []
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing.extend(new_questions)
        existing.sort(key=lambda q: q.get("id", 0))
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)


def process_subject(subject, progress):
    if not claim_subject(subject):
        return

    print(f"\n[{subject}] claimed by {MACHINE_ID}")
    questions, seen_ids = verify_and_load(subject)
    total = len(questions)

    subj_prog = progress.get(subject, {"done": False, "total": 0})
    if subj_prog.get("done") and total > 0:
        print(f"[{subject}] already complete ({total} questions), skipping")
        progress[subject] = {"done": True, "total": total}
        save_progress(progress)
        release_subject(subject)
        return

    if total > 0:
        print(f"[{subject}] resuming from {total} questions")

    no_new_streak = 0

    for round_num in range(1, MAX_ROUNDS + 1):
        renew_lock(subject)  # keep lock alive
        data = smart_request(subject)
        new = [q for q in data if q["id"] not in seen_ids]

        if new:
            for q in new:
                seen_ids.add(q["id"])
            total += len(new)
            no_new_streak = 0
            append_questions(subject, new)
            print(f"[{subject}] round {round_num}: +{len(new)} (total {total})")
        else:
            no_new_streak += 1
            print(f"[{subject}] round {round_num}: no new ({no_new_streak}/{NO_NEW_LIMIT})")
            if no_new_streak >= NO_NEW_LIMIT:
                print(f"[{subject}] exhausted")
                break

        with progress_lock:
            progress[subject] = {"done": no_new_streak >= NO_NEW_LIMIT, "total": total}
        save_progress(progress)
        time.sleep(DELAY)

    with progress_lock:
        progress[subject] = {"done": True, "total": total}
    save_progress(progress)
    release_subject(subject)
    print(f"[{subject}] done: {total} questions")


# --- Main ---
os.makedirs(OUTPUT_DIR, exist_ok=True)
progress = load_progress()

prevent_sleep()
prevent_shutdown()
# One thread per subject — all 24 run fully in parallel
threads = [
    threading.Thread(target=process_subject, args=(s, progress), daemon=True)
    for s in SUBJECTS
]
for t in threads:
    t.start()
for t in threads:
    t.join()
allow_sleep()
allow_shutdown()

print("\nAll done!")

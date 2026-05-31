import subprocess
import time
import os
import json

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
Q_DIR = os.path.join(REPO_DIR, "questions")
CHECK_INTERVAL = 30  # check every 30 seconds

def run(cmd):
    result = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True, shell=True)
    return result.stdout.strip(), result.stderr.strip()

def get_snapshot():
    snapshot = {}
    if not os.path.exists(Q_DIR):
        return snapshot
    for f in os.listdir(Q_DIR):
        if f.endswith(".json"):
            try:
                with open(os.path.join(Q_DIR, f), encoding="utf-8") as jf:
                    snapshot[f] = len(json.load(jf))
            except:
                snapshot[f] = 0
    return snapshot

def push():
    total = 0
    subjects = []
    for f in os.listdir(Q_DIR):
        if f.endswith(".json"):
            try:
                with open(os.path.join(Q_DIR, f), encoding="utf-8") as jf:
                    count = len(json.load(jf))
                    total += count
                    subjects.append(f"{f.replace('.json', '')}({count})")
            except:
                pass

    run("git add .")

    out, _ = run("git status --porcelain")
    if not out.strip():
        print("  nothing to commit")
        return

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] {total} questions | {', '.join(subjects)}"
    out, err = run(f'git commit -m "{msg}"')
    print(f"  commit: {out or err}")

    out, err = run("git push origin master")
    if "error" in err.lower():
        print(f"  push failed: {err}")
    else:
        print(f"  pushed ok")

print("Auto-push started — watching for changes every 30 seconds...\n")

last_snapshot = get_snapshot()

while True:
    time.sleep(CHECK_INTERVAL)
    current_snapshot = get_snapshot()

    if current_snapshot != last_snapshot:
        added = sum(current_snapshot.get(f, 0) - last_snapshot.get(f, 0) for f in current_snapshot)
        print(f"[{time.strftime('%H:%M:%S')}] change detected (+{added} questions), pushing...")
        push()
        last_snapshot = current_snapshot
    else:
        print(f"[{time.strftime('%H:%M:%S')}] no change")

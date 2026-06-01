import subprocess
import time
import os
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
Q_DIR = os.path.join(REPO_DIR, "questions")
DEBOUNCE = 5        # seconds after last change before pushing
PULL_INTERVAL = 60  # pull every 60 seconds to sync from other machines

# Only these paths get staged — temp/probe files are never committed
TRACKED = [
    "questions/",
    "progress.json",
    "subject_locks.json",
    "download.py",
    "autopush.py",
    "sort_questions.py",
    "signup_bot.py",
    "requirements.txt",
    "setup.bat",
    ".gitignore",
]

def run(cmd):
    result = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True, shell=True)
    return result.stdout.strip(), result.stderr.strip()

def pull():
    # only stash if there are actual uncommitted changes
    status, _ = run("git status --porcelain")
    has_changes = bool(status.strip())
    if has_changes:
        run("git stash")

    out, err = run("git pull origin master --rebase")

    if has_changes:
        _, pop_err = run("git stash pop")
        if "conflict" in pop_err.lower():
            run("git checkout stash -- .")
            run("git stash drop")

    if "conflict" in out.lower() or "conflict" in err.lower():
        print("  pull conflict, resetting to remote...")
        run("git rebase --abort")
        run("git reset --hard origin/master")
    elif "error" in err.lower():
        print(f"  pull error: {err}")
    elif "Already up to date" not in out:
        print(f"  pulled: {out}")

def push():
    total = 0
    subjects = []
    for f in sorted(os.listdir(Q_DIR)):
        if f.endswith(".json"):
            try:
                with open(os.path.join(Q_DIR, f), encoding="utf-8") as jf:
                    count = len(json.load(jf))
                    total += count
                    subjects.append(f"{f.replace('.json', '')}({count})")
            except:
                pass

    # only stage tracked paths — never temp/probe files
    for path in TRACKED:
        run(f"git add {path}")

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
        print("  pushed ok")

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_change = None
        self.pending = False

    def on_modified(self, event):
        if event.is_directory:
            return
        if ".git" in event.src_path or "autopush.py" in event.src_path:
            return
        self.last_change = time.time()
        if not self.pending:
            self.pending = True

    on_created = on_modified

handler = ChangeHandler()
observer = Observer()
observer.schedule(handler, REPO_DIR, recursive=True)
observer.start()

print("Auto-push started — watching for file changes + pulling every 60s...\n")

last_pull = time.time()

try:
    while True:
        now = time.time()

        if now - last_pull >= PULL_INTERVAL:
            pull()
            last_pull = time.time()

        if handler.pending and handler.last_change:
            if now - handler.last_change >= DEBOUNCE:
                print(f"[{time.strftime('%H:%M:%S')}] change detected, pushing...")
                push()
                handler.pending = False
                handler.last_change = None

        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
    print("\nStopped.")

observer.join()

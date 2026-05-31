import subprocess
import time
import os
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
Q_DIR = os.path.join(REPO_DIR, "questions")
DEBOUNCE = 5  # wait 5 seconds after last change before pushing (avoids mid-write pushes)

def run(cmd):
    result = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True, shell=True)
    return result.stdout.strip(), result.stderr.strip()

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

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_change = None
        self.pending = False

    def on_modified(self, event):
        if event.is_directory:
            return
        # ignore .git folder and autopush script itself
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

print("Auto-push started — watching for file changes...\n")

try:
    while True:
        if handler.pending and handler.last_change:
            elapsed = time.time() - handler.last_change
            if elapsed >= DEBOUNCE:
                print(f"[{time.strftime('%H:%M:%S')}] change detected, pushing...")
                push()
                handler.pending = False
                handler.last_change = None
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
    print("\nStopped.")

observer.join()

import json
import os

FOLDER = "New folder"

for filename in sorted(os.listdir(FOLDER)):
    if not filename.endswith(".json"):
        continue
    filepath = os.path.join(FOLDER, filename)
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        if not data:
            print(f"{filename}: empty, skipping")
            continue

        # sort by existing id first to preserve order
        data.sort(key=lambda q: int(q.get("id", 0)))

        # renumber from 1
        for i, q in enumerate(data, start=1):
            q["id"] = i

        tmp = filepath + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, filepath)

        print(f"{filename}: {len(data)} questions renumbered 1-{len(data)}")

    except Exception as e:
        print(f"{filename}: ERROR - {e}")

print("\nDone.")

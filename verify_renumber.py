import json
import os

FOLDER = "New folder"

all_good = True

for filename in sorted(os.listdir(FOLDER)):
    if not filename.endswith(".json"):
        continue
    filepath = os.path.join(FOLDER, filename)
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        if not data:
            print(f"{filename}: EMPTY")
            all_good = False
            continue

        ids = [q.get("id") for q in data]
        expected = list(range(1, len(data) + 1))

        if ids == expected:
            print(f"{filename}: OK — {len(data)} questions, ids 1-{len(data)}")
        else:
            all_good = False
            # find first mismatch
            mismatches = [(i+1, ids[i]) for i in range(len(ids)) if ids[i] != expected[i]]
            print(f"{filename}: FAIL — {len(data)} questions | first mismatch at position {mismatches[0][0]}: got id={mismatches[0][1]}, expected {mismatches[0][0]}")

    except Exception as e:
        print(f"{filename}: ERROR - {e}")
        all_good = False

print(f"\n{'All files verified OK!' if all_good else 'Some files have issues — re-run renumber.py'}")

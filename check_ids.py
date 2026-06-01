import json, os

for fname in os.listdir('questions'):
    if not fname.endswith('.json'):
        continue
    with open(f'questions/{fname}', encoding='utf-8') as f:
        d = json.load(f)
    if not d:
        print(fname, 'EMPTY')
        continue
    ids = [q['id'] for q in d[:5]]
    print(f'{fname}: {len(d)} questions | id type={type(d[0]["id"]).__name__} | sample ids={ids}')
    break  # just need one file

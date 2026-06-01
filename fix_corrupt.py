import re, json

def resolve_conflicts(text):
    pattern = re.compile(r'<<<<<<< [^\n]*\n(.*?)=======.*?>>>>>>> [^\n]*\n', re.DOTALL)
    prev = None
    while prev != text:
        prev = text
        text = pattern.sub(lambda m: m.group(1), text)
    # Remove any remaining orphaned conflict marker lines
    text = re.sub(r'^<<<<<<< [^\n]*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'^>>>>>>> [^\n]*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'^=======\n', '', text, flags=re.MULTILINE)
    return text

for subject in ['economics', 'mathematics', 'physics']:
    corrupt_path = f'questions/{subject}.json.corrupt'
    main_path = f'questions/{subject}.json'

    with open(corrupt_path, encoding='utf-8') as f:
        raw = f.read()

    cleaned = resolve_conflicts(raw)

    remaining = cleaned.count('<<<<<<<') + cleaned.count('>>>>>>>')
    if remaining:
        print(f'{subject}: WARNING - {remaining} conflict markers still remain after cleanup')
        continue

    try:
        new_data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f'{subject}: JSON error after cleaning: {e}')
        # Write cleaned to temp file for inspection
        with open(f'debug_{subject}_cleaned.json', 'w', encoding='utf-8') as f:
            f.write(cleaned)
        continue

    with open(main_path, encoding='utf-8') as f:
        main_data = json.load(f)

    existing_ids = {q['id'] for q in main_data}
    new_questions = [q for q in new_data if q['id'] not in existing_ids]

    print(f'{subject}: main={len(main_data)}, corrupt={len(new_data)}, new to add={len(new_questions)}')

    if new_questions:
        merged = main_data + new_questions
        with open(main_path, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f'{subject}: merged -> {len(merged)} total questions')
    else:
        print(f'{subject}: no new questions to add')

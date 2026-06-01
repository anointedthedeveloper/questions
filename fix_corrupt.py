import re, json

def resolve_conflicts(text):
    # Keep applying until no more conflict markers remain
    pattern = re.compile(r'<<<<<<< [^\n]*\n(.*?)=======.*?>>>>>>> [^\n]*\n', re.DOTALL)
    prev = None
    while prev != text:
        prev = text
        text = pattern.sub(lambda m: m.group(1), text)
    return text

for subject in ['economics', 'mathematics', 'physics']:
    corrupt_path = f'questions/{subject}.json.corrupt'
    main_path = f'questions/{subject}.json'

    with open(corrupt_path, encoding='utf-8') as f:
        raw = f.read()

    cleaned = resolve_conflicts(raw)

    remaining = cleaned.count('<<<<<<<') + cleaned.count('>>>>>>>') 
    if remaining:
        print(f'{subject}: WARNING - {remaining} conflict markers still remain')
        # Show first remaining
        idx = cleaned.find('<<<<<<<')
        if idx == -1:
            idx = cleaned.find('>>>>>>>')
        print(repr(cleaned[max(0,idx-50):idx+200]))
        continue

    try:
        new_data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f'{subject}: JSON error after cleaning: {e}')
        print(repr(cleaned[max(0,e.pos-100):e.pos+200]))
        continue

    # Load existing main file
    with open(main_path, encoding='utf-8') as f:
        main_data = json.load(f)

    existing_ids = {q['id'] for q in main_data}
    new_questions = [q for q in new_data if q['id'] not in existing_ids]

    print(f'{subject}: main={len(main_data)}, corrupt={len(new_data)}, new to add={len(new_questions)}')

    if new_questions:
        merged = main_data + new_questions
        with open(main_path, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f'{subject}: merged {len(new_questions)} new questions -> {len(merged)} total')
    else:
        print(f'{subject}: no new questions to add')

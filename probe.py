import requests, re

BASE = 'https://questions.aloc.com.ng'
s = requests.Session()
r = s.get(f'{BASE}/secure/signup', timeout=15)

# extract full form
form = re.search(r'<form[^>]*action[^>]*signup[^>]*>(.*?)</form>', r.text, re.DOTALL)
if form:
    print('FORM HTML:')
    print(form.group(0))
else:
    # find all inputs
    inputs = re.findall(r'<input[^>]+>', r.text)
    print('ALL INPUTS:')
    for i in inputs:
        print(i)

import requests, re, random, string

BASE = 'https://questions.aloc.com.ng'

s = requests.Session()
r = s.get(BASE + '/secure/signup', timeout=15)
token = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
rand = ''.join(random.choices(string.ascii_lowercase, k=8))
email = f'testbot_{rand}@mailinator.com'
password = 'password123'

resp = s.post(BASE + '/secure/signup', data={
    '_token': token, 'name': f'Bot {rand}',
    'email': email, 'password': password,
    'password_confirmation': password
}, timeout=15, allow_redirects=True)
print('signup:', resp.url)

r2 = s.get(BASE + '/admin/access-token', timeout=15)
with open('at.html', 'wb') as f:
    f.write(r2.content)

# strip to readable text
import re
body = re.search(r'<body[^>]*>(.*?)</body>', r2.text, re.DOTALL)
text = re.sub(r'<[^>]+>', ' ', body.group(1)) if body else r2.text
text = re.sub(r'\s+', ' ', text).strip()
print(text[:3000])

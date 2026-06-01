import requests, re, random, string

BASE = 'https://questions.aloc.com.ng'

s = requests.Session()
r = s.get(BASE + '/secure/signup', timeout=15)
token = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
rand = ''.join(random.choices(string.ascii_lowercase, k=8))
email = f'testbot_{rand}@mailinator.com'

resp = s.post(BASE + '/secure/signup', data={
    '_token': token,
    'name': f'Bot {rand}',
    'email': email,
    'password': 'password123',
    'password_confirmation': 'password123'
}, timeout=15, allow_redirects=True)

print('signup url:', resp.url)

# fetch access-token page
r2 = s.get(BASE + '/admin/access-token', timeout=15)
print('access-token page status:', r2.status_code)
with open('access_token.html', 'wb') as f:
    f.write(r2.content)

apis = re.findall(r'(QB-[A-Za-z0-9]+|ALOC-[A-Za-z0-9]+)', r2.text)
print('api keys:', apis)

# broader search
toks = re.findall(r'[A-Z]{2,5}-[A-Za-z0-9]{10,}', r2.text)
print('token patterns:', toks)

import requests, re, random, string, time

BASE = 'https://questions.aloc.com.ng'
start = time.time()
s = requests.Session()
r = s.get(BASE + '/secure/signup', timeout=15)
token = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
rand = ''.join(random.choices(string.ascii_lowercase, k=8))
resp = s.post(BASE + '/secure/signup', data={
    '_token': token, 'name': f'Bot {rand}',
    'email': f'testbot_{rand}@mailinator.com',
    'password': 'password123', 'password_confirmation': 'password123'
}, timeout=15, allow_redirects=True)
r2 = s.get(BASE + '/admin/access-token', timeout=15)
elapsed = time.time() - start
print(f'time: {elapsed:.2f}s | url: {resp.url}')
apis = re.findall(r'(QB-[A-Za-z0-9]+|ALOC-[A-Za-z0-9]+)', r2.text)
print('key:', apis)

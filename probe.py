import requests, re, random, string

BASE = 'https://questions.aloc.com.ng'

# --- signup ---
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

# --- logout ---
s.get(BASE + '/secure/logout', timeout=15)

# --- login ---
s2 = requests.Session()
r2 = s2.get(BASE + '/secure/login', timeout=15)
token2 = re.search(r'name="_token"\s+value="([^"]+)"', r2.text).group(1)
resp2 = s2.post(BASE + '/secure/login', data={
    '_token': token2, 'email': email, 'password': password
}, timeout=15, allow_redirects=True)
print('login:', resp2.url)

# --- get api key ---
r3 = s2.get(BASE + '/admin/access-token', timeout=15)
apis = re.findall(r'(QB-[A-Za-z0-9]+|ALOC-[A-Za-z0-9]+)', r3.text)
print('api key after login:', apis)

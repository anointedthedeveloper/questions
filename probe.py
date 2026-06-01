import requests, re, random, string

BASE = 'https://questions.aloc.com.ng'
s = requests.Session()

# get signup page + csrf
r = s.get(f'{BASE}/secure/signup', timeout=15)
token = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
print('csrf token:', token[:20], '...')

# generate random test account
rand = ''.join(random.choices(string.ascii_lowercase, k=8))
email = f'testbot_{rand}@mailinator.com'
password = 'TestPass123!'
name = f'Test Bot {rand}'

print(f'signing up: {email}')

resp = s.post(f'{BASE}/secure/signup', data={
    '_token': token,
    'name': name,
    'email': email,
    'password': password,
}, timeout=15, allow_redirects=True)

print('signup resp status:', resp.status_code)
print('signup resp url:', resp.url)
print('signup resp snippet:', resp.text[:800])

# look for API key patterns
apis = re.findall(r'(QB-[A-Za-z0-9]+|ALOC-[A-Za-z0-9]+)', resp.text)
print('api keys found:', apis)

# look for all secure routes
routes = re.findall(r'/secure/([a-z\-]+)', resp.text)
print('secure routes:', list(set(routes)))

# look for AccessToken or token fields
tokens = re.findall(r'(?:AccessToken|access.token|api.key)[^<]{0,100}', resp.text, re.IGNORECASE)
print('token refs:', tokens[:5])

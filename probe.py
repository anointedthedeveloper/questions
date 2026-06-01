import requests, re

BASE = 'https://questions.aloc.com.ng'
s = requests.Session()

# get login page + csrf
r = s.get(f'{BASE}/secure/login', timeout=15)
token = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)

# login with dummy creds just to see redirect/response structure
resp = s.post(f'{BASE}/secure/login', data={
    '_token': token,
    'email': 'test@test.com',
    'password': 'wrongpass123'
}, timeout=15, allow_redirects=True)
print('login resp status:', resp.status_code)
print('login resp url:', resp.url)
print('login resp snippet:', resp.text[:500])

# find all secure routes from the page
routes = re.findall(r'/secure/([a-z\-]+)', resp.text)
print('secure routes found:', list(set(routes)))

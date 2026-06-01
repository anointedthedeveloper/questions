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

print('url:', resp.url)
print('status:', resp.status_code)

# save dashboard
with open('dashboard.html', 'wb') as f:
    f.write(resp.content)

# look for api key patterns
apis = re.findall(r'(QB-[A-Za-z0-9]+|ALOC-[A-Za-z0-9]+)', resp.text)
print('api keys:', apis)

# look for AccessToken
toks = re.findall(r'AccessToken[^<]{0,100}', resp.text, re.IGNORECASE)
print('AccessToken refs:', toks[:5])

# look for any long alphanumeric token
long_toks = re.findall(r'[A-Za-z0-9]{20,}', resp.text)
print('long tokens sample:', long_toks[:10])

import requests, re, random, string

BASE = 'https://questions.aloc.com.ng'
s = requests.Session()

# signup
r = s.get(BASE + '/secure/signup', timeout=15)
token = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)

rand = ''.join(random.choices(string.ascii_lowercase, k=8))
email = f'testbot_{rand}@mailinator.com'
print('signing up:', email)

resp = s.post(BASE + '/secure/signup', data={
    '_token': token,
    'name': f'Bot {rand}',
    'email': email,
    'password': 'TestPass123!'
}, timeout=15, allow_redirects=True)

print('signup url:', resp.url, '| status:', resp.status_code)
apis = re.findall(r'(QB-[A-Za-z0-9]+|ALOC-[A-Za-z0-9]+)', resp.text)
print('api keys on redirect page:', apis)

# save redirect page
with open('after_signup.html', 'wb') as f:
    f.write(resp.content)

# check home
r2 = s.get(BASE, timeout=15)
apis2 = re.findall(r'(QB-[A-Za-z0-9]+|ALOC-[A-Za-z0-9]+)', r2.text)
print('home api keys:', apis2)

# look for any token-like strings
toks = re.findall(r'[A-Z]{2,5}-[a-f0-9]{16,}', resp.text)
print('token-like strings:', toks[:5])

# check error/success messages
msgs = re.findall(r'class="[^"]*alert[^"]*"[^>]*>(.*?)</div>', resp.text, re.DOTALL)
for m in msgs:
    print('ALERT:', re.sub(r'<[^>]+>', '', m).strip())

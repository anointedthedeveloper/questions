import requests, re, random, string

BASE = 'https://questions.aloc.com.ng'

def try_signup(extra_fields={}):
    s = requests.Session()
    r = s.get(BASE + '/secure/signup', timeout=15)
    token = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
    rand = ''.join(random.choices(string.ascii_lowercase, k=8))
    email = f'testbot_{rand}@mailinator.com'
    data = {'_token': token, 'name': f'Bot {rand}', 'email': email, 'password': 'TestPass123!'}
    data.update(extra_fields)
    resp = s.post(BASE + '/secure/signup', data=data, timeout=15, allow_redirects=True)
    msgs = re.findall(r'class="[^"]*alert[^"]*"[^>]*>(.*?)</div>', resp.text, re.DOTALL)
    alert = re.sub(r'<[^>]+>', '', msgs[0]).strip() if msgs else 'no alert'
    apis = re.findall(r'(QB-[A-Za-z0-9]+|ALOC-[A-Za-z0-9]+)', resp.text)
    print(f'  url={resp.url} | alert={alert} | apis={apis}')
    return resp, s

print('Test 1: with password_confirmation')
try_signup({'password_confirmation': 'TestPass123!'})

print('Test 2: simple password no special chars')
s2 = requests.Session()
r2 = s2.get(BASE + '/secure/signup', timeout=15)
t2 = re.search(r'name="_token"\s+value="([^"]+)"', r2.text).group(1)
rand = ''.join(random.choices(string.ascii_lowercase, k=8))
resp2 = s2.post(BASE + '/secure/signup', data={
    '_token': t2, 'name': f'Bot {rand}',
    'email': f'testbot_{rand}@mailinator.com',
    'password': 'password123',
    'password_confirmation': 'password123'
}, timeout=15, allow_redirects=True)
msgs2 = re.findall(r'class="[^"]*alert[^"]*"[^>]*>(.*?)</div>', resp2.text, re.DOTALL)
alert2 = re.sub(r'<[^>]+>', '', msgs2[0]).strip() if msgs2 else 'no alert'
apis2 = re.findall(r'(QB-[A-Za-z0-9]+|ALOC-[A-Za-z0-9]+)', resp2.text)
print(f'  url={resp2.url} | alert={alert2} | apis={apis2}')

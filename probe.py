import requests, re, random, string

BASE = 'https://questions.aloc.com.ng'

def try_signup(password, extra={}):
    s = requests.Session()
    r = s.get(BASE + '/secure/signup', timeout=15)
    token = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
    rand = ''.join(random.choices(string.ascii_lowercase, k=8))
    data = {'_token': token, 'name': f'Bot {rand}',
            'email': f'aloc_{rand}@mailinator.com',
            'password': password, 'password_confirmation': password}
    data.update(extra)
    resp = s.post(BASE + '/secure/signup', data=data, timeout=15, allow_redirects=True)
    alert = re.search(r'class="[^"]*alert[^"]*"[^>]*>(.*?)</div>', resp.text, re.DOTALL)
    msg = re.sub(r'<[^>]+>', '', alert.group(1)).strip() if alert else 'no alert'
    print(f'  pw={password!r:20} url={resp.url.split("/")[-1]:20} msg={msg}')
    return resp

# test various password formats
try_signup('Pass_abcd1234')       # bot format with underscore
try_signup('password123')         # what worked before
try_signup('Passabcd1234')        # no special char
try_signup('pass_abcd1234')       # lowercase
try_signup('Pass1234')            # short

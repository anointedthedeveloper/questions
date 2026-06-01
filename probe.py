import requests, re, sys

s = requests.Session()
r = s.get('https://questions.aloc.com.ng/secure/login', timeout=15)
print('status:', r.status_code)
print('len:', len(r.text))

for pat in [r'name="_token"\s+value="([^"]+)"', r'_token.*?value="([^"]+)"']:
    t = re.search(pat, r.text, re.DOTALL)
    if t:
        print('token:', t.group(1))
        break
else:
    print('token: NOT FOUND')

print('cookies:', dict(s.cookies))

# check dashboard
r2 = s.get('https://questions.aloc.com.ng/secure/dashboard', timeout=15)
print('dashboard status:', r2.status_code)
apis = re.findall(r'(QB-[A-Za-z0-9]+|ALOC-[A-Za-z0-9]+)', r2.text)
print('api keys on dashboard:', apis[:5])

# check profile
r3 = s.get('https://questions.aloc.com.ng/secure/profile', timeout=15)
print('profile status:', r3.status_code)
apis2 = re.findall(r'(QB-[A-Za-z0-9]+|ALOC-[A-Za-z0-9]+)', r3.text)
print('api keys on profile:', apis2[:5])

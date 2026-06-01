import requests
import re
import os
import sys
import argparse
from dotenv import dotenv_values

BASE = 'https://questions.aloc.com.ng'
ENV_FILE = '.env'


def get_csrf(session, url):
    r = session.get(url, timeout=15)
    m = re.search(r'name="_token"\s+value="([^"]+)"', r.text)
    if not m:
        raise RuntimeError(f'Could not find CSRF token on {url}')
    return m.group(1)


def signup(name, email, password):
    s = requests.Session()
    token = get_csrf(s, f'{BASE}/secure/signup')
    resp = s.post(f'{BASE}/secure/signup', data={
        '_token': token,
        'name': name,
        'email': email,
        'password': password,
        'password_confirmation': password,
    }, timeout=15, allow_redirects=True)

    if '/admin/dashboard' not in resp.url:
        alert = re.search(r'class="[^"]*alert[^"]*"[^>]*>(.*?)</div>', resp.text, re.DOTALL)
        msg = re.sub(r'<[^>]+>', '', alert.group(1)).strip() if alert else 'unknown error'
        raise RuntimeError(f'Signup failed: {msg}')

    print(f'[+] Signed up: {email}')
    return s


def login(email, password):
    s = requests.Session()
    token = get_csrf(s, f'{BASE}/secure/login')
    resp = s.post(f'{BASE}/secure/login', data={
        '_token': token,
        'email': email,
        'password': password,
    }, timeout=15, allow_redirects=True)

    if '/admin/dashboard' not in resp.url:
        raise RuntimeError('Login failed — check credentials')

    print(f'[+] Logged in: {email}')
    return s


def get_api_key(session):
    r = session.get(f'{BASE}/admin/access-token', timeout=15)
    keys = re.findall(r'(QB-[A-Za-z0-9]+|ALOC-[A-Za-z0-9]+)', r.text)
    if not keys:
        raise RuntimeError('Could not find API key on access-token page')
    return keys[0]


def save_to_env(key):
    existing = dotenv_values(ENV_FILE) if os.path.exists(ENV_FILE) else {}

    # find next available API_KEY_N slot
    n = 1
    while f'API_KEY_{n}' in existing:
        n += 1

    var_name = f'API_KEY_{n}'

    with open(ENV_FILE, 'a') as f:
        f.write(f'\n{var_name}={key}\n')

    print(f'[+] Saved to .env: {var_name}={key}')
    return var_name


def main():
    parser = argparse.ArgumentParser(description='Sign up on ALOC and store API key in .env')
    parser.add_argument('--name',     required=True, help='Full name')
    parser.add_argument('--email',    required=True, help='Email address')
    parser.add_argument('--password', required=True, help='Password')
    parser.add_argument('--login-only', action='store_true',
                        help='Skip signup, just login and fetch key')
    args = parser.parse_args()

    try:
        if args.login_only:
            session = login(args.email, args.password)
        else:
            session = signup(args.name, args.email, args.password)

        api_key = get_api_key(session)
        print(f'[+] API key: {api_key}')
        var = save_to_env(api_key)
        print(f'\nDone. Add {var} to your API_KEYS list in download.py')

    except RuntimeError as e:
        print(f'[-] Error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()

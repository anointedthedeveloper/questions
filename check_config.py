from dotenv import dotenv_values

_env = dotenv_values('.env')
API_KEYS = [v for k, v in sorted(_env.items()) if k.startswith('API_KEY_')]
print(f'loaded {len(API_KEYS)} API keys')
print(f'first: {API_KEYS[0]}')
print(f'last:  {API_KEYS[-1]}')

SUBJECTS = [
    'mathematics', 'english', 'chemistry', 'physics', 'biology',
    'economics', 'government', 'englishlit', 'geography',
    'commerce', 'accounting', 'civiledu', 'agricultural-science',
    'crk', 'irk',
    'further-mathematics', 'computer-studies', 'home-economics',
    'yoruba', 'igbo', 'hausa', 'currentaffairs', 'history', 'insurance'
]
RATE_LIMIT = 58
DELAY = max(60 / (RATE_LIMIT * len(API_KEYS)), 0.05)
print(f'workers (subjects in parallel): {len(SUBJECTS)}')
print(f'delay per request: {DELAY:.4f}s')
print(f'max throughput: {len(API_KEYS) * RATE_LIMIT} req/min')

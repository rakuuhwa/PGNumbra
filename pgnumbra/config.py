import json
import os

# Configuration with default values
from mrmime import init_mr_mime

cfg = {
    'accounts_file': 'accounts.csv',
    'proxies_file': '',
    'scan_retries': 3,
    'include_nearby': False,
    'pokemon_name_format': 'full',
    'shadowcheck_threads': 10,
    # API related values, usually don't need to change them
    'login_retries': 3,
    'login_delay': 6
}


def cfg_get(key):
    return cfg[key]


def cfg_set(key, val):
    cfg[key] = val


file_path = os.path.join('config.json')
with open(file_path, 'r') as f:
    user_cfg = json.loads(f.read())
    cfg.update(user_cfg)

init_mr_mime({
    'login_delay': cfg['login_delay'],
    'login_retries': cfg['login_retries']
})

import json
import os

cfg = {
    'accounts_file': 'accounts.csv',
    'proxies_file': '',
    'scan_retries': 3,
    'include_nearby': False,
    'pokemon_name_format': 'full',
    'shadowcheck_threads': 10
}


def cfg_get(key):
    return cfg[key]


def cfg_set(key, val):
    cfg[key] = val


file_path = os.path.join('config.json')
with open(file_path, 'r') as f:
    user_cfg = json.loads(f.read())
    cfg.update(user_cfg)

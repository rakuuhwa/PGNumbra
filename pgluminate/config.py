import json
import os

# Configuration with default values
cfg = {
    'proxies_file': '',
    'wait_after_login': 10,
    'include_nearby': False,
    'pokemon_name_format': 'full'
}


def cfg_get(key):
    return cfg[key]


file_path = os.path.join('config.json')
with open(file_path, 'r') as f:
    user_cfg = json.loads(f.read())
    cfg.update(user_cfg)

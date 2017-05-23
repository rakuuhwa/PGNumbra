import logging
import os
from Queue import Queue
from multiprocessing.pool import ThreadPool
from threading import Thread

from pgluminate.Torch import Torch
from pgluminate.config import cfg_get
from pgluminate.proxy import init_proxies

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [%(threadName)16s][%(module)14s][%(levelname)8s] %(message)s')

log = logging.getLogger(__name__)

# Silence some loggers
logging.getLogger('pgoapi.pgoapi').setLevel(logging.WARNING)

FILE_PREFIX = 'accounts'

# Shadowbanned accounts cannot see these Pokemon
HIDDEN_POKEMON = [
    7,
    13,
    21,
    48,
    75,
    79,
    95,
    111,
    138,
    140,
    162,
    170,
    184,
    213,
    216,
    223,
    224,
    226
]


def remove_account_file(suffix):
    fname = '{}-{}.csv'.format(FILE_PREFIX, suffix)
    if os.path.isfile(fname):
        os.remove(fname)


def check_account(torch):
    torch.scan_once()
    f = None
    if torch.pokemon:
        if is_blind(torch):
            log.info("Account {} is shadowbanned. :-(".format(torch.username))
            f = file_blinded
        else:
            log.info("Account {} is clean. :-)".format(torch.username))
            f = file_good
    else:
        log.error("Account {} could not scan location: {}".format(torch.username, torch.last_msg))
        f = file_error
    f.write('{},{},{}\n'.format(torch.auth, torch.username, torch.password))
    del torch.api
    del torch


def is_blind(torch):
    for pid in torch.pokemon:
        if pid in HIDDEN_POKEMON:
            return False
    return True


log.info("ShadowCheck starting up.")

lat = cfg_get('latitude')
lng = cfg_get('longitude')

remove_account_file('good')
file_good = open("{}-{}.csv".format(FILE_PREFIX, 'good'), 'a')
remove_account_file('blind')
file_blinded = open("{}-{}.csv".format(FILE_PREFIX, 'blind'), 'a')
remove_account_file('error')
file_error = open("{}-{}.csv".format(FILE_PREFIX, 'error'), 'a')

init_proxies()

torches = []
check_queue = Queue()
with open(cfg_get('accounts_file'), 'r') as f:
    for num, line in enumerate(f, 1):
        fields = line.split(",")
        fields = map(str.strip, fields)
        torch = Torch(fields[0], fields[1], fields[2], lat, lng)
        torches.append(torch)

pool = ThreadPool(cfg_get('checkonce_threads'))
pool.map(check_account, torches)
pool.close()
pool.join()

log.info("All accounts processed.")

file_good.close()
file_blinded.close()
file_error.close()
import logging
import os
from Queue import Queue
from multiprocessing.pool import ThreadPool
from threading import Thread

from pgluminate.Torch import Torch
from pgluminate.config import cfg_get, cfg_set
from pgluminate.proxy import init_proxies

# ===========================================================================

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [%(threadName)16s][%(module)14s][%(levelname)8s] %(message)s')

log = logging.getLogger(__name__)

# Silence some loggers
logging.getLogger('pgoapi.pgoapi').setLevel(logging.WARNING)

# ===========================================================================

FILE_PREFIX = 'accounts'

COMMON_POKEMON = [
    16,     # Pidgey
    19,     # Rattata
    23,     # Ekans
    27,     # Sandshrew
    29,     # Nidoran F
    32,     # Nidoran M
    41,     # Zubat
    43,     # Oddish
    46,     # Paras
    52,     # Meowth
    54,     # Psyduck
    60,     # Poliwag
    69,     # Bellsprout
    72,     # Tentacool
    74,     # Geodude
    81,     # Magnemite
    98,     # Krabby
    118,    # Goldeen
    120,    # Staryu
    129,    # Magikarp
    161,    # Sentret
    165,    # Ledyba
    167,    # Spinarak
    177,    # Natu
    183,    # Marill
    187,    # Hoppip
    191,    # Sunkern
    194,    # Wooper
    198,    # Murkrow
    209,    # Snubbull
    218     # Slugma
]

# Shadowbanned accounts cannot see these Pokemon - INCOMPLETE
HIDDEN_POKEMON = [
    7,      # Squirtle
    13,     # Weedle
    20,     # Raticate
    21,     # Spearow
    22,     # Fearow
    48,     # Venonat
    66,     # Machop
    70,     # Weepinbell
    75,     # Graveler
    79,     # Slowpoke
    90,     # Shellder
    92,     # Gastly
    93,     # Haunter
    95,     # Onix
    109,    # Koffing
    111,    # Rhyhorn
    116,    # Horsea
    122,    # Mr. Mime
    123,    # Scyther
    124,    # Jynx
    130,    # Gyarados
    133,    # Eevee
    138,    # Omanyte
    140,    # Kabuto
    143,    # Snorlax
    152,    # Chikorita
    162,    # Furret
    163,    # Hoothoot
    166,    # Ledian
    168,    # Ariados
    170,    # Chinchou
    184,    # Azumarill
    185,    # Sudowoodo
    213,    # Shuckle
    216,    # Teddiursa
    219,    # Magcargo
    223,    # Remoraid
    224,    # Octillery
    226     # Mantine
]
acc_stats = {
    'good': 0,
    'blind': 0,
    'error': 0
}

# ===========================================================================


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
            save_to_file(torch, 'blind')
        else:
            log.info("Account {} is good. :-)".format(torch.username))
            save_to_file(torch, 'good')
    else:
        log.error("Account {} could not scan location: {}".format(torch.username, torch.last_msg))
        save_to_file(torch, 'error')
    del torch.api
    del torch


def save_to_file(torch, suffix):
    global acc_stats
    acc_stats[suffix] = acc_stats.get(suffix, 0) + 1
    with open("{}-{}.csv".format(FILE_PREFIX, suffix), 'a') as f:
        f.write(
            '{},{},{}\n'.format(torch.auth_service, torch.username, torch.password))
        f.close()


def is_blind(torch):
    for pid in torch.pokemon:
        if pid not in COMMON_POKEMON:
            return False
    return True

# ===========================================================================

log.info("ShadowCheck starting up.")

lat = cfg_get('latitude')
lng = cfg_get('longitude')

remove_account_file('good')
remove_account_file('blind')
remove_account_file('error')

init_proxies()

# This test must include nearby Pokemon to work properly.
cfg_set('include_nearby', True)

torches = []
check_queue = Queue()
with open(cfg_get('accounts_file'), 'r') as f:
    for num, line in enumerate(f, 1):
        fields = line.split(",")
        fields = map(str.strip, fields)
        torches.append(Torch(fields[0], fields[1], fields[2], lat, lng))

num_threads = cfg_get('checkonce_threads')
log.info("Checking {} accounts with {} threads.".format(len(torches), num_threads))
pool = ThreadPool(num_threads)
pool.map(check_account, torches)
pool.close()
pool.join()

log.info(
    "All {} accounts processed. Detected {} GOOD, {} BLIND ones and {} with ERRORs.".format(
        len(torches), acc_stats['good'], acc_stats['blind'], acc_stats['error']))

if acc_stats['good'] == 0:
    log.warning("================= WARNING =================")
    log.warning("NONE of the accounts saw ANY rare Pokemon.")
    log.warning("Either they are all blind or there are in fact")
    log.warning("no rare Pokemon near this location right now.")
    log.warning("Try again with a different location to be sure.")

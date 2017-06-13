import logging
import os
from Queue import Queue
from multiprocessing.pool import ThreadPool
from threading import Lock

from pgnumbra.SingleLocationScanner import SingleLocationScanner
from pgnumbra.config import cfg_get, cfg_set
from pgnumbra.proxy import init_proxies, get_new_proxy

# ===========================================================================

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [%(threadName)16s][%(module)14s][%(levelname)8s] %(message)s')

log = logging.getLogger(__name__)

# Silence some loggers
logging.getLogger('pgoapi').setLevel(logging.WARNING)

# ===========================================================================

FILE_PREFIX = 'accounts'
ACC_INFO_FILE = FILE_PREFIX + '-info.txt'

COMMON_POKEMON = [
    16,     # Pidgey
    19,     # Rattata
    23,     # Ekans
    27,     # Sandshrew
    29,     # Nidoran F
    32,     # Nidoran M
    37,     # Vulpix
    41,     # Zubat
    43,     # Oddish
    46,     # Paras
    52,     # Meowth
    54,     # Psyduck
    58,     # Growlithe
    60,     # Poliwag
    69,     # Bellsprout
    72,     # Tentacool
    74,     # Geodude
    77,     # Ponyta
    81,     # Magnemite
    90,     # Shellder
    98,     # Krabby
    118,    # Goldeen
    120,    # Staryu
    129,    # Magikarp
    155,    # Cyndaquil
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
    218,    # Slugma
    220,    # Swinub
    228     # Houndour
]

acc_stats = {
    'good': 0,
    'blind': 0,
    'captcha': 0,
    'banned': 0,
    'error': 0
}

# ===========================================================================


def remove_account_file(suffix):
    fname = '{}-{}.csv'.format(FILE_PREFIX, suffix)
    if os.path.isfile(fname):
        os.remove(fname)


def check_account(torch):
    try:
        torch.scan_once()
    except Exception as e:
        log.exception("Error checking account {}".format(torch.username))

    try:
        if torch.pokemon:
            if is_blind(torch):
                log.info("Account {} is shadowbanned. :-(".format(torch.username))
                save_to_file(torch, 'blind')
            else:
                log.info("Account {} is good. :-)".format(torch.username))
                save_to_file(torch, 'good')
        else:
            if torch.is_banned():
                save_to_file(torch, 'banned')
            elif torch.has_captcha():
                save_to_file(torch, 'captcha')
            else:
                save_to_file(torch, 'error')
        save_account_info(torch)
    except Exception as e:
        log.exception(
            "Error saving checked account {} to file".format(torch.username))
    del torch


def write_line_to_file(fname, line):
    # Poor mans locking. Only 1 thread at any time, please. Super-defensive!
    if not hasattr(write_line_to_file, 'lock'):
        write_line_to_file.lock = Lock()
    write_line_to_file.lock.acquire()
    with open(fname, 'a') as f:
        f.write(line)
        f.close()
    write_line_to_file.lock.release()


def save_account_info(acc):
    global acc_info_tmpl

    def bool(x):
        return '' if x is None else ('Yes' if x else 'No')

    km_walked_f = acc.player_stats.get('km_walked')
    if km_walked_f:
        km_walked_str = '{:.1f} km'.format(km_walked_f)
    else:
        km_walked_str = ''
    line = acc_info_tmpl.format(
        acc.username,
        acc.player_stats.get('level', ''),
        acc.player_stats.get('experience', ''),
        bool(acc.is_warned()),
        bool(acc.is_banned()),
        bool(acc.has_captcha()),
        bool(is_blind(acc)),
        acc.player_stats.get('pokemons_encountered', ''),
        acc.player_stats.get('pokeballs_thrown', ''),
        acc.player_stats.get('pokemons_captured', ''),
        acc.player_stats.get('poke_stop_visits', ''),
        km_walked_str
    )
    write_line_to_file(ACC_INFO_FILE, line)


def init_account_info_file(torches):
    global acc_info_tmpl

    max_username_len = 4
    for t in torches:
        max_username_len = max(max_username_len, len(t.username))
    acc_info_tmpl = '{:' + str(
        max_username_len) + '} | {:3} | {:8} | {:4} | {:3} | {:7} | {:5} | {:6} | {:5} | {:5} | {:5} | {:10}\n'
    line = acc_info_tmpl.format(
        'Username',
        'Lvl',
        'XP',
        'Warn',
        'Ban',
        'Captcha',
        'Blind',
        'Enc',
        'Thr.',
        'Cap',
        'Spins',
        'Walked'
    )
    write_line_to_file(ACC_INFO_FILE, line)


def save_to_file(torch, suffix):
    global acc_stats
    acc_stats[suffix] = acc_stats.get(suffix, 0) + 1
    fname = "{}-{}.csv".format(FILE_PREFIX, suffix)
    line = '{},{},{}\n'.format(torch.auth_service, torch.username, torch.password)
    write_line_to_file(fname, line)


def is_blind(torch):
    # We don't know if we did not search/find ANY Pokemon
    if not torch.pokemon:
        return None

    for pid in torch.pokemon:
        if pid not in COMMON_POKEMON:
            return False
    return True


def log_results(key):
    if acc_stats[key]:
        log.info("{:7}: {}".format(key.upper(), acc_stats[key]))

# ===========================================================================

log.info("ShadowCheck starting up.")

lat = cfg_get('latitude')
lng = cfg_get('longitude')

# Delete result files.
remove_account_file('good')
remove_account_file('blind')
remove_account_file('captcha')
remove_account_file('banned')
remove_account_file('error')

if os.path.isfile(ACC_INFO_FILE):
    os.remove(ACC_INFO_FILE)

init_proxies()

# This test must include nearby Pokemon to work properly.
cfg_set('include_nearby', True)

torches = []
check_queue = Queue()
with open(cfg_get('accounts_file'), 'r') as f:
    for num, line in enumerate(f, 1):
        fields = line.split(",")
        fields = map(str.strip, fields)
        torches.append(
            SingleLocationScanner(fields[0], fields[1], fields[2], lat, lng,
                                  cfg_get('hash_key'), get_new_proxy()))

init_account_info_file(torches)

num_threads = cfg_get('shadowcheck_threads')
log.info("Checking {} accounts with {} threads.".format(len(torches), num_threads))
pool = ThreadPool(num_threads)
pool.map(check_account, torches)
pool.close()
pool.join()

log.info("All {} accounts processed.".format(len(torches)))
log_results('good')
log_results('blind')
log_results('captcha')
log_results('banned')
log_results('error')

if acc_stats['good'] == 0 and acc_stats['blind'] > 0:
    log.warning("================= WARNING =================")
    log.warning("NONE of the accounts saw ANY rare Pokemon.")
    log.warning("Either they are all blind or there are in fact")
    log.warning("no rare Pokemon near this location right now.")
    log.warning("Try again with a different location to be sure.")

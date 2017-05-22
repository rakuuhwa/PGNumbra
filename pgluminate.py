import logging
import time
from threading import Thread

from pgluminate.Torch import Torch
from pgluminate.config import cfg_get
from pgluminate.console import print_status
from pgluminate.proxy import init_proxies

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [%(threadName)16s][%(module)14s][%(levelname)8s] %(message)s')

log = logging.getLogger(__name__)

# Silence some loggers
logging.getLogger('pgoapi.pgoapi').setLevel(logging.WARNING)

torches = []

# ===========================================================================

log.info("PGLuminate starting up.")

lat = cfg_get('latitude')
lng = cfg_get('longitude')

init_proxies()

with open(cfg_get('accounts_file'), 'r') as f:
    for num, line in enumerate(f, 1):
        fields = line.split(",")
        fields = map(str.strip, fields)
        torch = Torch(fields[0], fields[1], fields[2], lat, lng)
        torches.append(torch)
        t = Thread(target=torch.run, name="{}".format(torch.username))
        t.daemon = True
        t.start()

# Start thread to print current status and get user input.
t = Thread(target=print_status,
           name='status_printer', args=(torches, "dummy"))
t.daemon = True
t.start()

# Dummy endless loop.
while True:
    time.sleep(1)

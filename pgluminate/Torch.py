import random
import time

import logging
from pgoapi import PGoApi
from pgoapi.exceptions import AuthException
from pgoapi.utilities import get_cell_ids, f2i

from pgluminate.config import cfg_get
from pgluminate.proxy import have_proxies, get_new_proxy
from pgluminate.utils import TooManyLoginAttempts, get_player_stats

log = logging.getLogger(__name__)


class Torch(object):
    def __init__(self, auth, username, password, latitude, longitude):
        self.auth = auth
        self.username = username
        self.password = password
        self.latitude = latitude
        self.longitude = longitude

        self.player_stats = {}
        self.pokemon = {}

        # Player State
        self.warned = None
        self.banned = None

        # Things needed for requests
        self.inventory_timestamp = None

        # instantiate pgoapi
        self.api = PGoApi()
        self.api.activate_hash_server(cfg_get('hash_key'))
        self.api.set_position(self.latitude, self.longitude, random.randrange(3, 170))
        self.last_request = None

        if have_proxies():
            self.proxy = get_new_proxy()
            self.log_info("Using Proxy: {}".format(self.proxy))
            self.api.set_proxy({
                'http': self.proxy,
                'https': self.proxy
            })

    def run(self):
        while True:
            self.check_login()
            self.scan_location()

    def scan_location(self):
        try:
            self.api.set_position(self.latitude, self.longitude, random.randint(12, 108))
            cell_ids = get_cell_ids(self.latitude, self.longitude)
            timestamps = [0, ] * len(cell_ids)
            req = self.api.create_request()
            req.get_map_objects(latitude=f2i(self.latitude), longitude=f2i(self.longitude),
                                since_timestamp_ms=timestamps,
                                cell_id=cell_ids)
            response = self.perform_request(req)

            self.wild_pokemon = self.count_pokemon(response)
        except Exception as e:
            pass

    def count_pokemon(self, response):
        self.pokemon = {}
        cells = response.get('responses', {}).get('GET_MAP_OBJECTS', {}).get('map_cells', [])
        for cell in cells:
            for p in cell.get('wild_pokemons', []):
                pid = p['pokemon_data']['pokemon_id']
                self.pokemon[pid] = self.pokemon.get(pid, 0) + 1
            if cfg_get('include_nearby'):
                for p in cell.get('nearby_pokemons', []):
                    pid = p['pokemon_id']
                    self.pokemon[pid] = self.pokemon.get(pid, 0) + 1

    # Updates warning/banned flags and tutorial state.
    def update_player_state(self):
        request = self.api.create_request()
        request.get_player(player_locale={'country': 'US', 'language': 'en',
                                          'timezone': 'America/Denver'})

        response = request.call().get('responses', {})

        get_player = response.get('GET_PLAYER', {})
        self.warned = get_player.get('warn', False)
        self.banned = get_player.get('banned', False)
        time.sleep(4)


    def check_login(self):
        # Logged in? Enough time left? Cool!
        if self.api._auth_provider and self.api._auth_provider._ticket_expire:
            remaining_time = self.api._auth_provider._ticket_expire / 1000 - time.time()
            if remaining_time > 60:
                self.log_debug(
                    'Credentials remain valid for another {} seconds.'.format(remaining_time))
                return

        # Try to login. Repeat a few times, but don't get stuck here.
        num_tries = 0
        # One initial try + login_retries.
        while num_tries < 3:
            try:
                self.api.set_authentication(
                    provider=self.auth,
                    username=self.username,
                    password=self.password)
                break
            except AuthException:
                num_tries += 1
                self.log_error(
                    'Failed to login. ' +
                    'Trying again in {} seconds.'.format(6))
                time.sleep(6)

        if num_tries >= 3:
            self.log_error(
                'Failed to login for {} tries. Giving up.'.format(
                    num_tries))
            raise TooManyLoginAttempts('Exceeded login attempts.')

        wait_after_login = cfg_get('wait_after_login')
        self.log_info('Login successful. Waiting {} more seconds.'.format(wait_after_login))
        time.sleep(wait_after_login)
        self.update_player_state()

    def perform_request(self, req, delay=12):
        req.check_challenge()
        req.get_hatched_eggs()
        if self.inventory_timestamp:
            req.get_inventory(last_timestamp_ms=self.inventory_timestamp)
        else:
            req.get_inventory()
        req.check_awarded_badges()
        req.get_buddy_walked()

        # Wait before we perform the request
        d = float(delay)
        if self.last_request and time.time() - self.last_request < d:
            time.sleep(d - (time.time() - self.last_request))
        response = req.call()
        self.last_request = time.time()

        # Update player stats
        self.player_stats = get_player_stats(response)

        # Update inventory timestamp
        try:
            self.inventory_timestamp = \
            response['GET_INVENTORY']['inventory_delta']['new_timestamp_ms']
        except KeyError:
            pass

        return response

    def log_info(self, msg):
        self.last_msg = msg
        log.info(msg)

    def log_debug(self, msg):
        self.last_msg = msg
        log.debug(msg)

    def log_warning(self, msg):
        self.last_msg = msg
        log.warning(msg)

    def log_error(self, msg):
        self.last_msg = msg
        log.error(msg)


import logging
import random
import time

from pgoapi.utilities import get_cell_ids, f2i

from pgluminate.POGOAccount import POGOAccount
from pgluminate.config import cfg_get

log = logging.getLogger(__name__)


class Torch(POGOAccount):
    def __init__(self, auth, username, password, latitude, longitude):
        super(Torch, self).__init__(auth, username, password)

        self.latitude = latitude
        self.longitude = longitude
        # Init API location
        self.api.set_position(self.latitude, self.longitude, random.randrange(3, 170))

        self.pokemon = {}

    def run(self):
        # Initial random delay to spread logins.
        time.sleep(random.randint(0, 10))
        while True:
            if self.check_login():
                self.scan_location()

    def scan_once(self):
        if self.check_login():
            self.scan_location()

    def scan_location(self):
        tries = 0
        max_tries = cfg_get("scan_retries")
        while tries < max_tries:
            tries += 1
            self.log_info("Scanning {}, {} (try #{})".format(self.latitude,
                                                             self.longitude,
                                                             tries))
            try:
                cell_ids = get_cell_ids(self.latitude, self.longitude)
                timestamps = [0, ] * len(cell_ids)
                responses = self.perform_request(
                    lambda req: req.get_map_objects(
                        latitude=f2i(self.latitude),
                        longitude=f2i(self.longitude),
                        since_timestamp_ms=timestamps, cell_id=cell_ids))

                self.count_pokemon(responses)
                if self.pokemon:
                    self.log_info("Successfully scanned location")
                    return
                else:
                    self.log_warning("Emtpy scan (try #{})".format(tries))
            except Exception as e:
                self.log_error(
                    "Error on get_map_objects (try #{}): {}".format(tries,
                                                                    repr(e)))

        self.log_error("Failed {} times. Giving up.".format(max_tries))

    def count_pokemon(self, response):
        self.pokemon = {}
        cells = response.get('GET_MAP_OBJECTS', {}).get('map_cells', [])
        for cell in cells:
            for p in cell.get('wild_pokemons', []):
                pid = p['pokemon_data']['pokemon_id']
                self.pokemon[pid] = self.pokemon.get(pid, 0) + 1
            if cfg_get('include_nearby'):
                for p in cell.get('nearby_pokemons', []):
                    pid = p['pokemon_id']
                    self.pokemon[pid] = self.pokemon.get(pid, 0) + 1


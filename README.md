# PGNumbra Tools
Tools that help in identifying and analyzing shadowbanned POGO accounts.

# Support the Author [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/slop)
If you like PGNumbra Tools and feel the urgent need to thank me, just drop me one or more **level 30 accounts** or buy me a **[PokeHash key](https://talk.pogodev.org/d/51-api-hashing-service-by-pokefarmer)**. Seriously, that would be so awesome! :-D You can find me on various Pokémon related Discords as "sLoPPydrive".

# Disclaimer
PGNumbra Tools or its author takes no responsibility if your accounts get banned in any way. As with any other 3rd party software breaking the ToS there is absolutely no guarantee that your accounts stay safe. This software is purely for educational purpose.

## Tool 1: `compare_scans.py`

A specific location gets scanned (`GET_MAP_OBJECTS` request) over and over again and the number of found Pokémon get compared in a table view. This way you can determine if some accounts are seeing more than others and also *what* they see exactly. Of course you should have at least one account that is not shadowbanned to see the difference.

## Tool 2: `shadowcheck.py`

A tool for mass-checking accounts. For every account exactly one `GET_MAP_OBJECTS` call is made to determine what Pokémon the account can see. If there is any of the rare Pokémon (which shadowbanned accounts cannot see) in the wild or nearby list, the account is considered **good**, otherwise **blind**. The tool sorts the accounts to files `acc-good.csv`, `acc-blind.csv` and `acc-error.csv` (in case of bans or other errors). Note that these files will be **overwritten** with each new run.

## Installation
Do the regular `pip install -r requirements.txt` stuff. That's it.

## Configuration
Both tools use the same configuration file. Just copy&edit `config.json.sample` to `config.json` and add some accounts and/or proxies to their respective files. Then run `python <script name>`. The configuration options are:

* `latitude`: Latitude of location to scan. **You should use a location where you are sure that a "rare" Pokémon is nearby.**
* `longitude`: Longitude of location to scan.
* `hash_key`: The Bossland PokéHash key to perform API requests.
* `accounts_file`: Name of a CSV file containing accounts in the format `<auth service>,<username>,<password>` - same as RocketMap
* `proxies_file`: File containing `<host>:<port>` proxies. Leave empty or remove this line if you don't use any proxies.
* `scan_retries`: How often the tools retry to scan the location. Defaults to `3`
* `include_nearby`: Whether to include nearby Pokémon in comparison or not. Defaults to `false`. Only relevant for `compare_scans.py`. `shadowcheck.py` always examines both wild and nearby Pokémon.
* `pokemon_name_format`: How Pokémon will be shown in the table of `compare_scans.py`. Can be one of `full` (full Pokémon name), `short` (name shortened to 3 letters) or `id` (Pokédex ID). Defaults to `full`
* `shadowcheck_threads`: How many parallel threads `shadowcheck.py` launches to test the accounts. Defaults to `10`, so 10 accounts will be tested simultaneously.
* `login_retries`: How often the tools will retry the login. Defaults to `3`.
* `login_delay`: How many seconds to wait between each login retry. Defaults to `6`.

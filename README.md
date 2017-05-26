# PGLuminate
Compares scan results of accounts to detect shadow bans.

A specific location gets scanned (`GET_MAP_OBJECTS` request) over and over again and the number of found Pokémon get compared in a table view. This way you can determine if some accounts are seeing more than others. Of course you shold have at least one account that is not shadow banned. Alternatively you have to be sure that the scanned location is in range of a rare Pokémon.

## Installation
Do the regular `pip install -r requirements.txt` stuff.

## Configuration
Just copy/edit `config.json.sample` to `config.json` and add some accounts and/or proxies to their respective files.

Then run `python  pgluminate.py'.
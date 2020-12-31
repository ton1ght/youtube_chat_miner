# YouTube Livestream Chat Data Mining Tool

**Disclaimer:** Using this tool is against the ToS of YouTube. Use at your own risk.

This tool allows you to data mine YouTube livestream chats without using their API. The messages, streams and authors are saved in a MariaDB database.

## Requirements

* Python3
* MariaDB instance (MySQL will probably work, too)

The following python modules are needed:

* [pytchat](https://pypi.org/project/pytchat/)
* [youtube-search-python](https://pypi.org/project/youtube-search-python/)
* [mariadb](https://pypi.org/project/mariadb/)
* [logging](https://pypi.org/project/logging/)

## Usage

```text
usage: fetch.py [-h] [--port PORT] [--pages PAGES]
                IP USER PASSWORD DB_NAME SEARCH_TERM

Fetch YouTube livestream chats and store the data in a MariaDB
database.

positional arguments:
  IP             MariaDB database IP address.
  USER           MariaDB database user.
  PASSWORD       MariaDB database password.
  DB_NAME        MariaDB database name.
  SEARCH_TERM    YouTube search term to find livestream chats.

optional arguments:
  -h, --help     show this help message and exit
  --port PORT    MariaDB database port. (Default: 3306)
  --pages PAGES  Amount of pages to fetch. Each pages consists of 20
                 search results. (Default: 5)
```

## Notes

Special thanks to the developers of [pytchat](https://github.com/taizan-hokuto/pytchat) and  [youtube-search-python](https://github.com/alexmercerind/youtube-search-python) who made this possible **without** the need for the YouTube API.

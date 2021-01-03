import logging
import mariadb
import argparse

logging.basicConfig(
    format="%(asctime)s: %(message)s",
    encoding="utf-8",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)

parser = argparse.ArgumentParser(description='Fetch YouTube livestream chats and store the data in a MariaDB database.')
parser.add_argument('ip', metavar="IP", type=str, help='MariaDB database IP address.')
parser.add_argument('--port', default=3306, type=int, help='MariaDB database port. (Default: 3306)')
parser.add_argument('user', metavar="USER", type=str, help='MariaDB database user.')
parser.add_argument('password', metavar="PASSWORD", type=str, help='MariaDB database password.')
parser.add_argument('name', metavar="DB_NAME", type=str, help='MariaDB database name.')
parser.add_argument('search_term', metavar="SEARCH_TERM", type=str, help='YouTube search term to find livestream chats.')
parser.add_argument('--pages', type=int, default=5, help='Amount of pages to fetch. Each pages consists of 20 search results. (Default: 5)')
args = parser.parse_args()

try:
    logging.info("Connecting to database...")
    conn = mariadb.connect(
        user=args.user,
        password=args.password,
        host=args.ip,
        port=args.port,
        database=args.name,
    )
    cursor = conn.cursor()
    conn.autocommit = True
    logging.info("Connection successfull.")
except mariadb.Error as e:
    logging.exception(f"Error connecting to MariaDB Platform: {e}")
    exit(1)

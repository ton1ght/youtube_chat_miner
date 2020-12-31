#!/usr/bin/python

import logging
import time
import argparse
from typing import Union

import mariadb
import pytchat
from youtubesearchpython import CustomSearch


def insertInto(tableName: str, columns: list[str], data: tuple):
    if len(columns) != len(data):
        logging.error("Column size does not match size of provided data.")
        exit(1)
    command = "INSERT INTO {} (".format(tableName)
    for column in columns:
        command += column + ","
    command = command[:-1] + ") VALUES ("
    for i in range(len(columns)):
        command += "?, "
    command = command[:-2] + ")"
    try:
        cursor.execute(command, data)
    except mariadb.IntegrityError:
        logging.warning("Stream already present in database.")
    except mariadb.Error as e:
        logging.exception(f"{e}")


def getStreams(search_term: str, pages: int) -> list[str]:
    """Searches for livestreams on youtube for a given term

    Args:
        search_term (str): The term to be search for.

    Returns:
        List(str): List of livestream ids
    """
    logging.info("Searching for livestreams: {}".format(search_term))
    sids: list[str] = []
    search: CustomSearch = CustomSearch(search_term, searchPreferences="CAMSAkAB")
    result: Union[str, dict, None] = search.result(1)
    for i in range(pages):
        result: Union[str, dict, None] = search.result(1)
        if isinstance(result, dict):
            for stream in result["result"]:
                sid: str = stream["id"]
                sids.append(sid)
                insertInto(
                    "streams",
                    ["id", "channel", "title"],
                    (sid, stream["channel"]["name"], stream["title"]),
                )
            search.next()
    logging.info("Returning {} livestreams.".format(len(sids)))
    return sids


def getChats(search_term: str, pages: int):
    """This function is essentially an endless loop which fetches new messages
    for each chat and adds them to the database. After a period of time,
    getStreams is called again to have a fresh list of streamIds.
    """
    timeout: float = time.time() + 60 * 120  # 2h
    stream_ids: list[str] = getStreams("christmas", pages)
    sid2chat = dict()
    for sid in stream_ids:
        sid2chat[sid] = pytchat.create(video_id=sid)
    while True:
        i = 1
        if time.time() > timeout:
            logging.info("Fetching new streams because timeout reached.")
            getChats(search_term, pages)
        for sid in sid2chat:
            logging.info(
                "Fetching livestream chat: {} ({}/{})".format(sid, i, len(sid2chat))
            )
            if sid2chat[sid].is_alive():
                for c in sid2chat[sid].get().sync_items():
                    logging.info("      Received message:")
                    logging.info(
                        f"         {c.datetime} [{c.author.name}]- {c.message}"
                    )
                    insertInto(
                        "messages",
                        [
                            "chatType",
                            "message",
                            "sent",
                            "amountValue",
                            "currency",
                            "isVerified",
                            "isChatOwner",
                            "isChatSponsor",
                            "isChatModerator",
                            "channelName",
                            "channelId",
                            "streamId",
                        ],
                        (
                            c.type,
                            c.message,
                            c.datetime,
                            c.amountValue,
                            c.currency,
                            c.author.isVerified,
                            c.author.isChatOwner,
                            c.author.isChatSponsor,
                            c.author.isChatModerator,
                            c.author.name,
                            c.author.channelId,
                            sid,
                        ),
                    )
                    logging.info("      Added message to database.")
                i = i + 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch YouTube livestream chats and store the data in a MariaDB database.')
    parser.add_argument('ip', metavar="IP", type=str, help='MariaDB database IP address.')
    parser.add_argument('--port', default=3306, type=int, help='MariaDB database port. (Default: 3306)')
    parser.add_argument('user', metavar="USER", type=str, help='MariaDB database user.')
    parser.add_argument('password', metavar="PASSWORD", type=str, help='MariaDB database password.')
    parser.add_argument('name', metavar="DB_NAME", type=str, help='MariaDB database name.')
    parser.add_argument('search_term', metavar="SEARCH_TERM", type=str, help='YouTube search term to find livestream chats.')
    parser.add_argument('--pages', type=int, default=5, help='Amount of pages to fetch. Each pages consists of 20 search results. (Default: 5)')
    args = parser.parse_args()
    logging.basicConfig(
        format="%(asctime)s: %(message)s",
        encoding="utf-8",
        level=logging.INFO,
        datefmt="%H:%M:%S",
    )
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
        getChats(args.search_term, args.pages)
    except mariadb.Error as e:
        logging.exception(f"Error connecting to MariaDB Platform: {e}")
        exit(1)

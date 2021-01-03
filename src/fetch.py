import time
import logging
import pytchat
import mariadb
from typing import Union

import config
from youtubesearchpython import CustomSearch


def insertInto(tableName: str, columns: list[str], data: tuple):
    """Constructs query to insert data

    Args:
        tableName (str): The table in which the data should be inserted
        columns (list[str]): The columns to fill with data
        data (tuple): A tuple containing the data for the columns
    """
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
        config.cursor.execute(command, data)
    except mariadb.Error as e:
        logging.exception(f"{e}")


def getStreams() -> list[str]:
    """Searches for livestreams on youtube for a given term

    Returns:
        List(str): List of livestream ids
    """
    logging.info("Searching for livestreams: {}".format(config.args.search_term))
    sids: list[str] = []
    search: CustomSearch = CustomSearch(
        config.args.search_term, searchPreferences="CAMSAkAB"
    )
    result: Union[str, dict, None] = search.result(1)
    for i in range(config.args.pages):
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


def getChats():
    """This function is essentially an endless loop which fetches new messages
    for each chat and adds them to the database. After a period of time,
    getStreams is called again to have a fresh list of streamIds.
    """
    timeout: float = time.time() + 60 * 120  # 2h
    stream_ids: list[str] = getStreams()
    sid2chat = dict()
    for sid in stream_ids:
        sid2chat[sid] = pytchat.create(video_id=sid)
    while True:
        i = 1
        if time.time() > timeout:
            logging.info("Fetching new streams because timeout reached.")
            getChats()
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

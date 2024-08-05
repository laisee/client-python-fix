import os
from datetime import UTC, datetime

import jwt


def generateJWT(apikey: str, now):

    #
    # retrieve values from env variables
    #
    API_SECRET = os.getenv("API_SECRET", "DUMMY")
    URI = os.getenv("API_URI", "DUMMY")
    DURATION = int(os.getenv("JWT_DURATION", 86400000))

    payload = {
        "client": "api",
        "uri": URI,
        "nonce": now,
        "iat": now,
        "exp": now + DURATION,
        "sub": apikey,
    }
    try:
        return jwt.encode(payload, API_SECRET, algorithm="ES256")
    except Exception as err:
        print("Error: {}".format(err))
        exit(0)


def get_log_filename(prefix):
    # Get the current UTC datetime
    now_utc = datetime.utcnow()
    # Format the datetime into a string
    datetime_str = now_utc.strftime("%Y%m%d_%H%M%S")
    # Create the log file name
    filename = f"{prefix}_{datetime_str}.log"
    return filename


def get_attr(fix_message, key):
    """
    Extracts the value for a given key from a FIX message.

    :param fix_message: The FIX message string.
    :param key: The key for which to get the value.
    :return: The value associated with the key, or None if the key is not found.
    """
    return get_attrs(fix_message).get(key)


def get_attrs(fix_message):
    """
    Parses a FIX message with '|' as the separator into a dictionary of attributes.

    :param fix_message: The FIX message string.
    :return: A dictionary with attribute tags as keys and their values as values.
    """
    attributes = {}

    # Split the message by '|'
    parts = fix_message.strip().split("|")

    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            attributes[key] = value

    return attributes


def format_epoch_time(epoch_time):
    # Convert epoch time to datetime object
    dt = datetime.fromtimestamp(epoch_time, UTC)

    # Format datetime object as required string format
    return dt.strftime("%Y%m%d-%H:%M:%S.%f")[:-3]

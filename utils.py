import os
from datetime import UTC, datetime

import jwt


def generateJWT(apikey: str, now: int) -> str:
    """Generate a signed JWT token using environment configuration.

    Parameters
    ----------
    apikey:
        API key used as token subject.
    now:
        Current epoch time.

    Returns
    -------
    str
        Encoded JWT token string.
    """

    # retrieve values from env variables
    API_SECRET = os.getenv("API_SECRET")
    URI = os.getenv("API_URI")
    DURATION = int(os.getenv("JWT_DURATION", 86400000))

    if not API_SECRET:
        raise ValueError("API_SECRET environment variable is required")
    if not URI:
        raise ValueError("API_URI environment variable is required")

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
        raise ValueError(
            f"Error '{err}' while generating JWT token with APIKEY {apikey}"
        )


def get_log_filename(prefix: str) -> str:
    """Create a timestamped log filename.

    Parameters
    ----------
    prefix:
        Prefix for the log file name.

    Returns
    -------
    str
        Filename with UTC timestamp.
    """
    # Get the current UTC datetime
    now_utc = datetime.utcnow()
    # Format the datetime into a string
    datetime_str = now_utc.strftime("%Y%m%d_%H%M%S")
    # Create the log file name
    filename = f"{prefix}_{datetime_str}.log"
    return filename


def get_attr(fix_message: str, key: str) -> str | None:
    """
    Extracts the value for a given key from a FIX message.

    :param fix_message: The FIX message string.
    :param key: The key for which to get the value.
    :return: The value associated with the key, or None if the key is not found.
    """
    return get_attrs(fix_message).get(key)


def get_attrs(fix_message: str) -> dict[str, str]:
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


def format_epoch_time(epoch_time: int) -> str:
    """Return FIX timestamp string for a given epoch time."""
    # Convert epoch time to datetime object
    dt = datetime.fromtimestamp(epoch_time, UTC)

    # Format datetime object as required string format
    return dt.strftime("%Y%m%d-%H:%M:%S.%f")[:-3]

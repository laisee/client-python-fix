from datetime import datetime, UTC
import jwt
import os

def generateJWT(apikey: str, now):

    #
    # retrieve values from env variables
    #
    API_SECRET=os.getenv('API_SECRET',"DUMMY")
    URI=os.getenv('API_URI',"DUMMY")
    DURATION=int(os.getenv("JWT_DURATION",86400000))

    payload = {
        "client": "api",
        "uri": URI,
        "nonce": now,
        "iat": now,
        "exp": now + DURATION,
        "sub": apikey
    }
    try:
        return jwt.encode(payload, API_SECRET, algorithm="ES256")
    except Exception as err:
        print("Error: {}".format(err))
        exit(0)

def format_epoch_time(epoch_time):
    # Convert epoch time to datetime object
    dt = datetime.fromtimestamp(epoch_time, UTC)

    # Format datetime object as required string format
    return dt.strftime("%Y%m%d-%H:%M:%S.%f")[:-3]

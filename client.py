import asyncio
import logging
import os
import ssl
import sys
from websockets import connect

from dotenv import load_dotenv

from messages import (
    checkLogonMsg,
    getMsgCancel,
    getMsgHeartbeat,
    getMsgLogon,
    getMsgNewOrder,
)
from utils import get_log_filename

# Common settings
SEPARATOR = "\x01"
VERTLINE = "|"

load_dotenv()

# Create logger for PT Fix Client
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO
)  # Set console log cnfig to display all INFO & above logging messages

# Add file handler for logging client
file_handler = logging.FileHandler(
    get_log_filename(os.getenv("LOG_FILE", "powertrade_client"))
)
file_handler.setLevel(
    logging.DEBUG
)  # Set the file handler to the lowest level to capture all log entries

# Create loggin formatter and assign to file handler
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Add file handler to the logger
logger.addHandler(file_handler)

# first seqnum taken by LOGON message, incremented for new orders and heartbeats
seqnum = 2
async def send_heartbeat(ws, apikey: str) -> None:
    """Periodically send FIX heartbeat messages over the websocket."""
    global seqnum
    init_sleep = int(os.getenv("INIT_SLEEP", 60))
    await asyncio.sleep(init_sleep)
    heartbeat_sleep = int(os.getenv("HEARTBEAT_SLEEP", 90))
    while True:
        await asyncio.sleep(heartbeat_sleep)
        seqnum += 1
        msg = getMsgHeartbeat(apikey, seqnum)
        await ws.send(msg)
        logger.info("Sent heartbeat message")


async def main(server: str, port: int, apikey: str) -> None:
    """Connect to the FIX endpoint and submit a sample order."""
    global seqnum

    SYMBOL = "ETH-USD"
    PRICE = 2508.08
    QUANTITY = 0.1

    uri = f"wss://{server}:{port}"
    ssl_context = ssl.create_default_context()
    ssl_context.load_verify_locations(cafile=os.getenv("CERTFILE_LOCATION", "cert.crt"))

    async with connect(uri, ssl=ssl_context) as ws:
        msg = getMsgLogon(apikey)
        await ws.send(msg)
        response = await ws.recv()
        valid, error_msg = checkLogonMsg(response)
        if not valid:
            logger.error(f"Invalid Logon response: {error_msg}")
            return

        heartbeat_task = asyncio.create_task(send_heartbeat(ws, apikey))

        clOrdID, order_msg = getMsgNewOrder(SYMBOL, PRICE, QUANTITY, apikey, seqnum)
        await ws.send(order_msg)
        logger.info("Sent new order")

        resp = await ws.recv()
        logger.info(f"Order response: {resp}")

        cancel_id = 11111
        seqnum += 1
        _, cancel_msg = getMsgCancel(clOrdID, cancel_id, SYMBOL, apikey, seqnum)
        await ws.send(cancel_msg)
        logger.info("Sent cancel request")

        await asyncio.sleep(int(os.getenv("FINAL_SLEEP", 20)))
        heartbeat_task.cancel()



if __name__ == "__main__":

    # load env variables from .env file
    # after this call all values in .env file will be available as env vars
    load_dotenv()

    # assign server url or use default value
    server = os.getenv(
        "API_URL", "api.wss.test.power.trade"
    )  # use TEST system for Order Entry as default values

    # assign server port or use default value
    port = int(
        os.getenv("API_PORT", 2021)
    )  # assign port value from .env file or use default value

    # assign server url
    apikey = os.getenv(
        "API_KEY", None
    )  # default to None which will generate an Exception when value tested in code

    #
    # call main method() to run logon/add/cancel or cancel on logout order functions
    #
    try:
        asyncio.run(main(server, port, apikey))
    except SystemExit as e:
        print(f"Exiting with code {e.code}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

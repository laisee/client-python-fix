import asyncio
import logging
import os
import socket
import ssl
import sys
import threading
import time

from dotenv import load_dotenv

from messages import (
    checkMsg,
    checkLogonMsg,
    getMsgCancel,
    getMsgHeartbeat,
    getMsgLogon,
    getMsgNewOrder,
    translateFix,
)
from utils import get_attr, get_log_filename

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

# first seqnum taken by LOGON message, this var is incremented for new orders, heartbeat
seqnum = 2

# Event object to signal the heartbeat thread to stop
stop_event = threading.Event()


def send_heartbeat(apikey, conn):
    global seqnum
    seqnum += 1
    try:
        msg = getMsgHeartbeat(apikey, seqnum)
        conn.sendall(msg)
        logger.info(f"Sending Heartbeat Msg: {msg}")
        logger.info(f"Sent heartbeat message with Success @ seqnum {seqnum}")
    except Exception as e:
        logger.error(f"Failed to send Heartbeat message: error was '{e}'")


def heartbeat_thread(apikey, conn, stop_event):
    try:
        INIT_SLEEP = os.getenv(
            "INIT_SLEEP", 60
        )  # SLEEP for X seconds while client is starting up, default to 60 seconds
        time.sleep(INIT_SLEEP)
        HEARTBEAT_SLEEP = int(os.getenv("HEARTBEAT_SLEEP", 90))  # defaults to 90 secs
        while not stop_event.is_set():
            # delay start of thread by 20 secs
            send_heartbeat(apikey, conn)
            time.sleep(
                HEARTBEAT_SLEEP
            )  # Send heartbeat every `HEARTBEAT_SLEEP` seconds
    except Exception as e:
        print(f"Heartbeat thread exception: {e}")


async def main(server: str, port: int, apikey: str):
    global seqnum

    #
    # Trade test values
    # N.B. Not designed for PRODUCTION trading
    #
    RESP_SENDER = "PT-OE"
    SYMBOL: str = "ETH-USD"
    PRICE: float = 2508.08 #3090.00 + randint(1, 8)
    QUANTITY: float = .1

    # Define server address w/ port
    server_addr = f"{server}:{port}"
    logger.info(f"server: {server_addr}")

    # Create context for the TLS connection
    context = ssl.create_default_context()

    # Wrap the socket with SSL
    context.load_verify_locations(cafile=os.getenv("CERTFILE_LOCATION", "cert.crt"))
    logger.info("Context created")

    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # wait up to X secs for receiving responses
    logger.info( f"Assigning WAIT for Fix response messages of {os.getenv('MSG_RESPONSE_WAIT', 5)} seconds")
    sock.settimeout(int(os.getenv("MSG_RESPONSE_WAIT", 5)))

    print(f"connecting to {server} on port {port} ...")
    sock.connect((server, port))

    conn = context.wrap_socket(sock, server_hostname=server)

    try:
        print("Handshaking Fix SSL/TLS connection ...")
        conn.do_handshake()

        #  Check Fix API connection with Logon message
        msg = getMsgLogon(apikey)
        error_msg = ""
        try:
            print(f"Sending Logon request {msg} to server {server} ...")
            logger.debug(f"Sending Logon msg {msg} to server {server} ...")
            # send Fix Logon message
            conn.sendall(msg)

            print(f"Reading Logon response from server {server} ...")
            logger.debug(f"Reading Logon response from server {server} ...")
            response = conn.recv(1024)

            print(f"Checking Logon response from server {response} ...")
            valid, error_msg = checkLogonMsg(response)
            if valid:
                logger.info("Received valid Logon response")
                # Start heartbeat thread
                threading.Thread(
                    target=heartbeat_thread,
                    args=(
                        apikey,
                        conn,
                        stop_event,
                    ),
                ).start()
            else:
                logger.error(f"Invalid Logon response: error was '{error_msg}'")
                sys.exit(1)

            clOrdID, msg = getMsgNewOrder(SYMBOL, PRICE, QUANTITY, apikey, seqnum)
            decoded_msg = msg.decode("utf-8")
            print(
                "Sending new order [%s] with order details: {%s}"
                % (clOrdID, decoded_msg)
            )
            logger.debug(
                "Sending new order [%s] with order details: {%s}"
                % (clOrdID, decoded_msg)
            )
            conn.sendall(msg)

            print("Reading New Order response from server ...")
            response = conn.recv(1024)

            logger.debug(f"Received(decoded): {response.decode('utf-8')}")
            valid = checkMsg(response, RESP_SENDER, apikey)
            (
                print("Received valid New Order response")
                if valid
                else print(f"Received invalid New Order response -> {response}")
            )

            #
            # iterate few times with sleep to allow trading messages from Limit Order to arrive
            #
            count = 0
            POLL_SLEEP = int(
                os.getenv("POLL_SLEEP", 5)
            )  # seconds to sleep between iterations
            POLL_LIMIT = int(os.getenv("POLL_LIMIT", 10))  # iteration count

            logger.info(
                f"Waiting for New Order [{clOrdID}] confirmation response from server [{count}] ..."
            )

            while count < POLL_LIMIT:
                time.sleep(POLL_SLEEP)
                try:
                    logger.info("Waiting for new message ...")
                    response = conn.recv(1024)
                    # response = await asyncio.get_event_loop().sock_recv(conn, 1024)
                    msg_str = response.decode("utf-8").replace(SEPARATOR, VERTLINE)
                    if msg_str is not None:
                        logger.info(f"Received(decoded):\n {msg_str}")
                        msg_list = msg_str.split("8=FIX.4.4")
                        for i, msg in enumerate(msg_list):
                            logger.debug(
                                "Recd msg: Ord '%s' Type [%s] Sts [%s]"
                                % (
                                    get_attr(msg_str, "11"),
                                    translateFix("35", get_attr(msg_str, "35")),
                                    translateFix("39", get_attr(msg_str, "39")),
                                )
                            )
                            if (
                                get_attr(msg, "35") == "8"
                                and translateFix("39", get_attr(msg, "39")) == "New"
                            ):
                                logger.info(
                                    "Exit Wait loop for order confirmation as received order status == 'New'"
                                )
                                count = POLL_LIMIT
                                break
                except Exception as e:
                    logger.error("Error while waiting for new message -> %s" % e)
                count += 1

            # setup cancel order to remove new order added above
            cancelOrderID = 11111 # clOrdID

            print(f"Sleep {POLL_SLEEP*5} secs before starting to Cancel orders")
            logger.info("Sleep before starting to Cancel orders")
            time.sleep(POLL_SLEEP * 5)
            #
            # Cancel Order can be done if the New Limit Order above is not filled
            #
            logger.debug("Building Cancel Order Message for order %s" % cancelOrderID)
            seqnum += 1
            now, msg = getMsgCancel(clOrdID, cancelOrderID, SYMBOL, apikey, seqnum)
            logger.debug(
                "Sending Cancel Order Message %s for order %s with Seqnum {seqnum}"
                % (msg, cancelOrderID)
            )
            conn.sendall(msg)

            #
            # Await response from order cancel message
            #
            count = 0
            POLL = True
            while POLL and count < POLL_LIMIT:
                time.sleep(POLL_SLEEP)
                logger.debug("Awaiting Cancel order response from server ...")
                response = conn.recv(1024)
                msg = response.decode("utf-8").replace(SEPARATOR, VERTLINE)
                logger.debug(
                    "Received msg from server with type [%s] status [%s]"
                    % (
                        translateFix("35", get_attr(msg, "35")),
                        translateFix("39", get_attr(msg, "39")),
                    )
                )

                #
                # was received message a 'heartbeat' [Msg Type = '0']
                #
                if get_attr(msg, "35") == "0":
                    logger.info("Heartbeat msg received ...")
                #
                # received message an 'execution report' [Msg Type = '8']
                #
                elif (
                    get_attr(msg, "35") == "8"
                    and translateFix("39", get_attr(msg, "39")) == "Cancelled"
                ):
                    logger.info(
                        "Received Order Cancel response with order status == 'Cancelled'"
                    )
                    POLL = False
                #
                # Check status of the order i.e. '2' for Filled, '8' for Rejected
                elif (
                    get_attr(msg, "35") == "9"
                    and translateFix("39", get_attr(msg, "39")) == "Rejected"
                ):
                    logger.info(
                        "Received Order Cancel response with order status == 'Rejected'"
                    )
                    POLL = False
                else:
                    logger.debug(
                        f"Received(decoded): {response.decode('utf-8').replace(SEPARATOR,VERTLINE)}"
                    )
                    logger.debug(
                        "Recd msg with type [%s] status [%s] for order %s"
                        % (
                            translateFix("35", get_attr(msg, "35")),
                            translateFix("39", get_attr(msg, "39")),
                            cancelOrderID,
                        )
                    )
                count += 1
        except socket.timeout:
            wait_time = os.getenv("MSG_RESPONSE_WAIT", 5)
            logger.info(f"Receive operation timed out after {wait_time} seconds.")
        except Exception as e:
            logger.error(f"Error while processing send/receive Fix messages: {e}")

    except Exception as e:
        logger.error(f"Failed to make Fix connection and send Order message: {e}")
    finally:
        #
        # Allow 'FINAL_SLEEP' seconds to pass so we can check account balance / possition changes / open orders before closing connection which will remove open orders
        #
        FINAL_SLEEP = int(os.getenv("FINAL_SLEEP", 20))
        logger.info(f"\nWaiting {FINAL_SLEEP} secs to close connection")
        stop_event.set()  # Signal the heartbeat thread to stop
        time.sleep(FINAL_SLEEP)
        sock.close()
        conn.close()
        logger.info(
            "\n**************************************************************************\n"
        )


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

import asyncio
from messages import checkMsg, getMsgCancel, getMsgNewOrder, getMsgLogon, translateFix
from dotenv import load_dotenv
import logging
from random import randint
import socket
import ssl
import sys
import time
import os

# Common settings
SEPARATOR = '\x01'
VERTLINE = '|'

load_dotenv()

# Create logger for this Client
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Set console log cnfig to display all INFO & above logging messages

# Create a file handler
file_handler = logging.FileHandler(os.getenv('LOG_FILE', 'pt.app.log'))
file_handler.setLevel(logging.DEBUG)  # Set the file handler to the lowest level to capture all log entries

# Create a formatter and set it for the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(file_handler)

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
    parts = fix_message.strip().split('|')
    
    for part in parts:
        if '=' in part:
            key, value = part.split('=', 1)
            attributes[key] = value
    
    return attributes

async def main(server: str, port: int, apikey: str):
    #
    # Trade test values
    # N.B. Do NOT use in PRODUCTION
    #
    RESP_SENDER = "PT-OE"
    SYMBOL: str = "SOL-USD"
    PRICE: float = 190.00 + randint(1,8) 
    QUANTITY: float = 1.08

    seqnum = 2
    # Define the server address and port
    server_addr = f"{server}:{port}"
    logger.info(f"server: {server_addr}")

    # Create a context for the TLS connection
    # Wrap the socket with SSL
    context = ssl.create_default_context()
    context.load_verify_locations(cafile=os.getenv("CERTFILE_LOCATION", "test-cert.crt"))
    logger.info("Context created")

    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # wait up to X secs for receiving responses  
    logger.info(f"Assigning WAIT for Fix response messages of {os.getenv('MSG_RESPONSE_WAIT', 5)} seconds")
    sock.settimeout(os.getenv('MSG_RESPONSE_WAIT', 5))

    print(f"connecting to {server} on port {port} ...")
    sock.connect((server, port))
    
    conn = context.wrap_socket(sock, server_hostname=server)
    
    try:
        print("Handshaking Fix SSL/TLS connection ...")
        conn.do_handshake()
        
        #  Check Fix API connection with Logon message
        msg = getMsgLogon(apikey)
        try:
            logger.debug(f"Sending Logon request to server {server} ...")
            # send Fix Logon message 
            conn.sendall(msg)
        
            logger.debug(f"Reading Logon response from server {server} ...")
            response = conn.recv(1024)

            valid = checkMsg(response, RESP_SENDER, apikey)
            if valid: 
               logger.info("Received valid Logon response") 
            else:
               logger.error("Invalid Logon response, closing down client ")
               sys.exit(1)

            clOrdID, msg = getMsgNewOrder(SYMBOL, PRICE, QUANTITY, apikey, seqnum)
            decoded_msg = msg.decode('utf-8')
            logger.debug("Sending new order [%s] with order details: {%s}" % (clOrdID, decoded_msg))
            conn.sendall(msg)

            print("Reading New Order response from server ...")
            response = conn.recv(1024)

            logger.debug(f"Received(decoded): {response.decode('utf-8')}")
            valid = checkMsg(response, RESP_SENDER, apikey)
            print("Received valid Logon response") if valid else print("Received invalid Logon response -> {response}")

            logger.debug("Sending New Order message")
            clOrdID, msg = getMsgNewOrder(SYMBOL, PRICE, QUANTITY, apikey)
            logger.info(msg)
        
            #
            # iterate few times with sleep to allow trading messages from Limit Order to arrive
            #
            count = 0
            SLEEP = 5 # seconds to sleep between iterations. TODO - move to .env config file
            LIMIT = 10 # iteration count, TODO - move to .env config file

            logger.info(f"Waiting for New Order [{clOrdID}] confirmation response from server [{count}] ...")

            while (count < LIMIT):
                time.sleep(SLEEP)
                try:
                    logger.info("Waiting for new message ...")
                    response = conn.recv(1024)
                    #response = await asyncio.get_event_loop().sock_recv(conn, 1024)
                    msg_str = response.decode('utf-8').replace(SEPARATOR, VERTLINE)
                    if msg_str is not None:
                        logger.info(f"Received(decoded):\n {msg_str}")
                        msg_list = msg_str.split("8=FIX.4.4")
                        for i, msg in enumerate(msg_list):
                            logger.debug("Recd msg: Ord '%s' Type [%s] Sts [%s]" % (get_attr(msg_str,"11"), translateFix("35", get_attr(msg_str,"35")), translateFix("39", get_attr(msg_str, "39"))))
                            if  get_attr(msg,"35") == '8' and translateFix("39", get_attr(msg, "39")) == 'New':
                                logger.info("Exit Wait loop for order confirmation as received order status == 'New'") 
                                count = LIMIT
                                break
                except Exception as e:
                    logger.error("Error while waiting for new message -> %s" % e)

                # Sometimes multiple Fix messages received.
                # - split on initial tag to separate msgs
                count += 1

            # setup cancel order to remove new order added above
            cancelOrderID = clOrdID

            print("SLEEP XX secs before starting to Cancel orders")
            logger.info("SLEEP before starting to Cancel orders")
            time.sleep(SLEEP*5)
            # 
            # Cancel Order can be done if the New Limit Order above is not filled
            # 
            logger.debug("Building Cancel Order Message for order %s" % cancelOrderID)
            seqnum += 1
            now, msg = getMsgCancel(clOrdID, cancelOrderID, SYMBOL, apikey, seqnum)
            logger.debug("Sending Cancel Order Message %s for order %s" % (msg, cancelOrderID))
            conn.sendall(msg)

            #
            # Await response from order cancel message
            #
            count = 0
            POLL = True
            while POLL and count < LIMIT:
                time.sleep(SLEEP)
                logger.debug("Awaiting Cancel order response from server ...")
                response = conn.recv(1024)
                #response = await asyncio.get_event_loop().sock_recv(conn, 1024)
                msg = response.decode('utf-8').replace(SEPARATOR,VERTLINE)
                logger.debug("Received msg from server with type [%s] status [%s]" % (translateFix("35", get_attr(msg,"35")), translateFix("39", get_attr(msg, "39"))))
                if get_attr(msg, "35") == "0":
                    logger.info("Heartbeat msg received ...")
                    pass
                if get_attr(msg,"35") == '8' and translateFix("39", get_attr(msg, "39")) == 'Cancelled':
                    logger.info("Exit loop for order cancellation - received order status == 'Cancelled'") 
                    POLL = False
                else:
                    logger.debug(f"Received(decoded): {response.decode('utf-8').replace(SEPARATOR,VERTLINE)}")
                    logger.debug("Recd msg with type [%s] status [%s] for order %s" % (translateFix("35", get_attr(msg,"35")), translateFix("39", get_attr(msg, "39")), cancelOrderID))
                count += 1
        except socket.timeout:
            logger.error("Received operation timed out after 60 seconds.")
        except Exception as e:
            logger.error(f"Error while processing send/receive Fix messages: {e}")
        
    except Exception as e:
        logger.error(f"Failed to make Fix connection and send Order message: {e}")
    finally:
        # 
        # Allow XX seconds to pass so we can check account balance / possition changes / open orders before closing connection which will remove open orders
        # 
        FINAL_SLEEP=int(os.getenv("FINAL_SLEEP", 20))
        logger.info(f"\nWaiting {FINAL_SLEEP} secs to close connection")
        time.sleep(FINAL_SLEEP)
        sock.close()
        conn.close()
        logger.info("\n**************************************************************************\n")

if __name__ == "__main__":

    # load env variables from .env file
    # after this call all values in .env file will be available as env vars
    load_dotenv()

    # assign server url or use default value
    server =os.getenv("API_URL", "api.wss.test.power.trade") # use TEST system for Order Entry as default values

    # assign server port or use default value
    port = int(os.getenv("API_PORT", 2021))                  # assign port value from .env file or use default value 

    # assign server url
    apikey = os.getenv("API_KEY", None)                      # default to None which will generate an Exception when value tested in code

    #
    # call main method() to run logon/add/cancel or cancel on logout order functions 
    #
    asyncio.run(main(server, port, apikey))

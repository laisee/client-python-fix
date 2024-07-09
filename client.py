<<<<<<< HEAD
import asyncio
from messages import checkMsg, getMsgCancel, getMsgRFQ, getMsgNewOrder, getMsgLOGON
import datetime
from dotenv import load_dotenv
import jwt
import logging
from random import randint
import re
from random import randint
import socket
import ssl
import sys
import time
import os

=======
import datetime
from dotenv import load_dotenv
import jwt
from random import randint
import re
import simplefix as sfx
import socket
import ssl
import time
import os

# TODO
# - logging
# - lint code
# - security checks 
# - refactor socket/connection code
# - load config from yaml files

>>>>>>> 0c20a51 (Add files via upload)
# Common settings
SEPARATOR = '\x01'
VERTLINE = '|'

<<<<<<< HEAD
# Create logger for this Client
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Set console log cnfig to display all INFO & above logging messages

# Create a file handler
file_handler = logging.FileHandler('client.log')
file_handler.setLevel(logging.DEBUG)  # Set the file handler to the lowest level to capture all log entries

# Create a formatter and set it for the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(file_handler)


def translate(key, value):
    trans=value
    if key == "35":
        if value == "0":
            trans = "Heartbeat"
        elif value == "1":
            trans = "Test Request"
        elif value == "2":
            trans = "Resend Request"
        elif value == "3":
            trans = "Reject"
        elif value == "4":
            trans = "Sequence Reset"
        elif value == "5":
            trans = "Logout"
        elif value == "A":
            trans = "Logon"
        elif value == "6":
            trans = "Indication of Interest"
        elif value == "7":
            trans = "Advertisement"
        elif value == "8":
            trans = "Execution Report"
        elif value == "9":
            trans = "Order Cancel Reject"
        elif value == "D":
            trans = "New Order - Single"
        elif value == "E":
            trans = "New Order - List"
        elif value == "F":
            trans = "Order Cancel Request"

    elif key == "39":
        if value == "0":
            trans = "New"
        elif value == "1":
            trans = "Partial Fill"
        elif value == "2":
            trans = "Filled"
        elif value == "3":
            trans = "Done for Day"
        elif value == "4":
            trans = "Cancelled"
        elif value == "5":
            trans = "Replaced"
        elif value == "6":
            trans = "Pending Cancel"
        elif value == "7":
            trans = "Stopped"
        elif value == "8":
            trans = "Rejected"
        elif value == "9":
            trans = "Suspended"
        elif value == "A":
            trans = "Pending New"
        elif value == "A":
            trans = "Pending New"
        elif value == "B":
            trans = "Calculated"
        elif value == "C":
            trans = "Expired"
        elif value == "D":
            trans = "Accepted for Bidding"
        elif value == "E":
            trans = "Pending Replace"
    return trans

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
=======
def checkMsg(msg: bytes, sender: str, target: str):

    count = 0
    assert msg is not None, "error - message cannot be None or empty string"

    fields = msg.decode("utf-8").replace(SEPARATOR,VERTLINE).split(VERTLINE)

    # check we received a Sender Comp ID 
    for field in fields:
        if re.search('49=',field) and sender in field:
            count += 1

    # check we received a Target Comp ID 
    for field in fields:
        if re.search('56=',field) and target in field:
            count += 1

    # require both to be present in message
    return True if count == 2 else False

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
    dt = datetime.datetime.fromtimestamp(epoch_time, datetime.UTC)

    # Format datetime object as required string format
    return dt.strftime("%Y%m%d-%H:%M:%S.%f")[:-3]

def getMsgLOGON(apikey: str):

    msg = sfx.FixMessage()
    now = int(time.time())

    assert apikey is not None, "Error - API KEY must not be empty or None"

    # Header
    msg.append_pair(8, "FIX.4.4", True)
    msg.append_pair(35,  "A", True)
    msg.append_pair(34,   1, True)
    msg.append_pair(49, apikey, True)
    msg.append_pair(52, format_epoch_time(now), True)
    msg.append_pair(56, "PT-OE", True)

    # Body
    msg.append_pair(98,   0)
    msg.append_pair(108, 30)
    msg.append_pair(141, "Y")
    msg.append_pair(554, generateJWT(apikey, now))

    print(msg)

    return msg.encode()

def getMsgNewOrder(symbol: str, price: float, quantity: float, apikey: str, seqNum: int = 2):

    msg = sfx.FixMessage()
    now = int(time.time())

    assert apikey is not None, "Error - API KEY must not be empty or None"
    assert price is not None, "Error - price must not be empty value or None"
    assert price > 0.00, "Error - price must be greater than zero"

    # Header
    msg.append_pair(8,    "FIX.4.4", True)
    msg.append_pair(35,   "D", True)
    msg.append_pair(34,   seqNum, True)
    msg.append_pair(49,   apikey, True)
    msg.append_pair(52,   format_epoch_time(now), True)
    msg.append_pair(56,   "PT-OE", True)

    # Body
    msg.append_pair(11,   now)
    msg.append_pair(38,   quantity)
    msg.append_pair(40,   2)
    msg.append_pair(44,   price)
    msg.append_pair(54,   1)
    msg.append_pair(55,   symbol)
    msg.append_pair(60,   format_epoch_time(now))

    return now, msg.encode()

def getMsgCancel(orderID: str, cancelOrderID:int, symbol: str, seqNum: int, quantity: float):

    assert orderID is not None, "Error - orderId must not be empty or None"

    msg = sfx.FixMessage()
    now = int(time.time())

    # Header
    msg.append_pair(8,   "FIX.4.4", True)
    #msg.append_pair(9,  373, True)
    msg.append_pair(35,  "F", True)
    msg.append_pair(34,  seqNum, True)
    msg.append_pair(56,  "PT-OE", True)

    # Body
    msg.append_pair(11,  cancelOrderID)          # <field name='ClOrdID' required='Y' />
    msg.append_pair(38,  quantity)               # <component name='OrderQtyData' required='Y' />
    msg.append_pair(41,  orderID)                # <field name='OrigClOrdID' required='Y' />
    msg.append_pair(54,  1)                      # <field name='Side' required='Y' />
    msg.append_pair(55,  symbol)                 # <component name='Instrument' required='Y' />
    msg.append_pair(60,  format_epoch_time(now)) # <field name='TransactTime' required='Y' />

    return msg.encode()


def main(server: str, port: int, apikey: str):
>>>>>>> 0c20a51 (Add files via upload)

    #
    # Trade test values
    # N.B. Do NOT use in PRODUCTION
    #
    RESP_SENDER = "PT-OE"
    SYMBOL: str = "SOL-USD"
<<<<<<< HEAD
    SYMBOL2: str = "AVAX-USD"
    PRICE: float = 190.00 + randint(1,8) 
    QUANTITY: float = 1.08

    seqnum = 2
    # Define the server address and port
    server_addr = f"{server}:{port}"
    logger.info(f"server: {server_addr}")
=======
    PRICE: float = 88.00
    QUANTITY: float = 1.00

    # Define the server address and port
    server_addr = f"{server}:{port}"
    print(f"server: {server_addr}")
>>>>>>> 0c20a51 (Add files via upload)
    
    # Create a context for the TLS connection
    # Wrap the socket with SSL
    context = ssl.create_default_context()
    context.load_verify_locations(cafile="api-test.crt")
<<<<<<< HEAD
    logger.info("Context created")
=======
    print("Context created")
>>>>>>> 0c20a51 (Add files via upload)

    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

<<<<<<< HEAD
    # wait up to 2 secs for receiving responses  
    sock.settimeout(2.0)

    logger.info(f"connecting to {server} on port {port} ...")
    sock.connect((server, port))
    
    conn = context.wrap_socket(sock, server_hostname=server)
    logger.info("Connection created -> %s" % conn)
    
    try:
        logger.info("Handshaking with server %s " % server)
        conn.do_handshake()
        
        # Send data to the server
        logger.info(f"Sending data to connection {conn}")
=======
    # wait up to 90 secs for receiving responses  
    sock.settimeout(90.0)

    print(f"connecting to {server} on port {port} ...")
    sock.connect((server, port))
    
    conn = context.wrap_socket(sock, server_hostname=server)
    print("Connection created -> ", conn)
    
    try:
        print("Handshaking ...")
        conn.do_handshake()
        
        # Send data to the server
        print("Sending data to server ...", conn)
>>>>>>> 0c20a51 (Add files via upload)

        #  Check Fix API connection with LOGON message
        msg = getMsgLOGON(apikey)
        try:
            # send Fix LOGON message 
            conn.sendall(msg)
        
<<<<<<< HEAD
            logger.info("Reading LOGON response from server ...")
            response = conn.recv(1024)

            valid = checkMsg(response, RESP_SENDER, apikey)
            if valid: 
               logger.info(f"Valid LOGON response") 
            else:
               logger.error(f"Invalid LOGON response, closing down client ")
               sys.exit(1)

            logger.info("Sending New Order (single leg) Message ")
            clOrdID, msg = getMsgNewOrder(SYMBOL, PRICE, QUANTITY, apikey, seqnum)
            decoded_msg = msg.decode('utf-8')
            logger.info("Sending new order [%s] with order details: {%s}" % (clOrdID, decoded_msg))
=======
            print("Reading response from server ...")
            response = conn.recv(1024)

            #print(f"Received(raw msg): {response}")
            #print(f"Received(decoded): {response.decode('utf-8')}")
            valid = checkMsg(response, RESP_SENDER, apikey)
            print(f"Received valid LOGON response") if valid else print("Received invalid LOGON response -> {response}")

            print("Sending New Order message")
            clOrdID, msg = getMsgNewOrder(SYMBOL, PRICE, QUANTITY, apikey)
            print(msg)
>>>>>>> 0c20a51 (Add files via upload)
            conn.sendall(msg)
        
            #
            # iterate few times with sleep to allow trading messages from Limit Order to arrive
            #
            count = 0
<<<<<<< HEAD
            SLEEP = 3 # seconds to sleep between iterations. TODO - move to .env config file
            MAX   = 10 # iteration count, TODO - move to .env config file

            logger.info(f"Waiting for New Order [{clOrdID}] confirmation response from server [{count}] ...")
            while (count < MAX):
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
                            logger.info("Received msg: Order '%s' type [%s] status [%s]" % (get_attr(msg_str,"11"), translate("35", get_attr(msg_str,"35")), translate("39", get_attr(msg_str, "39"))))
                            if  get_attr(msg,"35") == '8' and translate("39", get_attr(msg, "39")) == 'New':
                                logger.info("Exit Wait loop as Order Status == 'New'") 
                                break
                except Exception as e:
                    logger.error("Error while waiting for new message -> %s" % e)

                # Sometimes multiple Fix messages received.
                # - split on initial tag to separate msgs
                count += 1

            # setup cancel order to remove new order added above
            cancelOrderID = clOrdID;

            logger.info("SLEEP before starting to Cancel orders")
            time.sleep(SLEEP*3)
            # 
            # Cancel Order can be done if the New Limit Order above is not filled
            # 
            logger.info("Building Cancel Order Message for order %s" % cancelOrderID)
            seqnum += 1
            now, msg = getMsgCancel(clOrdID, cancelOrderID, SYMBOL, apikey, seqnum)
            logger.info("Sending Cancel Order Message %s for order %s" % (msg, cancelOrderID))
            conn.sendall(msg)

            #
            # Await response from order cancel message
            #
            WAIT = True;
            while WAIT:
                time.sleep(SLEEP)
                logger.info("Awaiting Cancel order response from server ...")
                response = conn.recv(1024)
                #response = await asyncio.get_event_loop().sock_recv(conn, 1024)
                msg = response.decode('utf-8').replace(SEPARATOR,VERTLINE)
                logger.info("Received msg from server with type [%s] status [%s]" % (translate("35", get_attr(msg,"35")), translate("39", get_attr(msg, "39"))))
                if get_attr(msg, "35") == "0":
                    logger.info("Heartbeat msg received ...")
                    pass
                else:
                    logger.info(f"Received(decoded): {response.decode('utf-8').replace(SEPARATOR,VERTLINE)}")
                    logger.info("Recd msg with type [%s] status [%s] for order %s" % (translate("35", get_attr(msg,"35")), translate("39", get_attr(msg, "39")), cancelOrderID))
                    WAIT = False

        except socket.timeout:
            logger.error("Received operation timed out after 60 seconds.")
        except Exception as e:
            logger.error(f"Error while processing send/receive Fix messages: {e}")
        
    except Exception as e:
        logger.error(f"Failed to connect & send message: {e}")
=======
            SLEEP = 5 # seconds
            MAX = 5 # iteration count

            print(f"Receiving response from server [{count}] ...")
            while (count<MAX):
                time.sleep(SLEEP)
                response = conn.recv(1024)
                msg_str = response.decode('utf-8').replace(SEPARATOR,VERTLINE)
                msg_list = msg_str.split("8=FIX.4.4")
                for i, msg in enumerate(msg_list):
                    print(f"Received(decoded) {i} :\n {msg}")
                count += 1
                print(f"Received response from server[{count}] ...")

            cancelOrderID = randint(1000000, 1999999)
            seqNum = 3

            # 
            # Cancel Order can be done if the New Limit Order above is not filled
            # 
            #print("Building Cancel Order Message for order '{orderId}'")
            #msg = getMsgCancel(clOrdID, cancelOrderID, SYMBOL, seqNum, QUANTITY)
            #print(msg)
            #conn.sendall(msg)

            #print("Reading response from server ...")
            #response = conn.recv(1024)
            #print(f"Received(decoded): {response.decode('utf-8').replace(SEPARATOR,VERTLINE)}")

        except socket.timeout:
            print("Receive operation timed out after 60 seconds.")
        
    except Exception as e:
        print(f"Failed to connect & send message: {e}")
>>>>>>> 0c20a51 (Add files via upload)
        
    finally:
        # 
        # Allow 30 seconds to pass so we can check account balance / possition changes / open orders before closing connection which will remove open orders
        # 
<<<<<<< HEAD
        logger.info("\nWaiting 30 secs to close connection")
        time.sleep(30)
        sock.close()
        conn.close()
        logger.info("\n**************************************************************************\n")
=======
        print("Waiting 30 secs to close connection")
        time.sleep(30)
        sock.close()
        conn.close()
>>>>>>> 0c20a51 (Add files via upload)

if __name__ == "__main__":

    # load env variables from .env file
    # after this call all values in .env file will be available as env vars
    load_dotenv()

    # assign server url or use default value
    server =os.getenv("API_URL", "api.wss.test.power.trade") # use TEST system for Order Entry as default values

    # assign server port or use default value
    port = int(os.getenv("API_PORT", 2021))                  # assign port value from .env file or use default value 

    # assign server url or use default value
    apikey = os.getenv("API_KEY", None)                      # default to None which will generate an Exception when value tested in code

    #
<<<<<<< HEAD
    # call main method() to run logon/add/cancel or cancel on logout order functions 
    #
    asyncio.run(main(server, port, apikey))
=======
    # call main method() with values for server/port/apikey
    #
    main(server, port, apikey)
>>>>>>> 0c20a51 (Add files via upload)

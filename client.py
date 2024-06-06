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

# Common settings
SEPARATOR = '\x01'
VERTLINE = '|'

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

    #
    # Trade test values
    # N.B. Do NOT use in PRODUCTION
    #
    RESP_SENDER = "PT-OE"
    SYMBOL: str = "SOL-USD"
    PRICE: float = 88.00
    QUANTITY: float = 1.00

    # Define the server address and port
    server_addr = f"{server}:{port}"
    print(f"server: {server_addr}")
    
    # Create a context for the TLS connection
    # Wrap the socket with SSL
    context = ssl.create_default_context()
    context.load_verify_locations(cafile="api-test.crt")
    print("Context created")

    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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

        #  Check Fix API connection with LOGON message
        msg = getMsgLOGON(apikey)
        try:
            # send Fix LOGON message 
            conn.sendall(msg)
        
            print("Reading response from server ...")
            response = conn.recv(1024)

            #print(f"Received(raw msg): {response}")
            #print(f"Received(decoded): {response.decode('utf-8')}")
            valid = checkMsg(response, RESP_SENDER, apikey)
            print(f"Received valid LOGON response") if valid else print("Received invalid LOGON response -> {response}")

            print("Sending New Order message")
            clOrdID, msg = getMsgNewOrder(SYMBOL, PRICE, QUANTITY, apikey)
            print(msg)
            conn.sendall(msg)
        
            #
            # iterate few times with sleep to allow trading messages from Limit Order to arrive
            #
            count = 0
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
        
    finally:
        # 
        # Allow 30 seconds to pass so we can check account balance / possition changes / open orders before closing connection which will remove open orders
        # 
        print("Waiting 30 secs to close connection")
        time.sleep(30)
        sock.close()
        conn.close()

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
    # call main method() with values for server/port/apikey
    #
    main(server, port, apikey)

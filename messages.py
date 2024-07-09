from utils import format_epoch_time, generateJWT
import simplefix as sfx
import re
import time

SEPARATOR = '\x01'
VERTLINE='|'

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
    return msg.encode()

def getMsgNewOrder(symbol: str, price: float, quantity: float, apikey: str, seqnum: int = 2):

    msg = sfx.FixMessage()
    now = int(time.time())

    assert apikey is not None, "Error - API KEY must not be empty or None"
    assert price is not None, "Error - price must not be empty value or None"
    assert price > 0.00, "Error - price must be greater than zero"

    # Header
    msg.append_pair(8,    "FIX.4.4", True)
    msg.append_pair(35,   "D", True)
    msg.append_pair(34,   seqnum, True)
    msg.append_pair(49,   apikey, True)
    msg.append_pair(52,   format_epoch_time(now), True)
    msg.append_pair(56,   "PT-OE", True)

    # Body
    msg.append_pair(11,   now)                      # ClOrdID
    msg.append_pair(38,   quantity)                 # Order Quantity
    msg.append_pair(40,   2)                        # OrdType (1 = Market, 2 = Limit)
    msg.append_pair(44,   price)                    # Order Price
    msg.append_pair(54,   2)                        # Side (1 = BUY, 2 = SELL)
    msg.append_pair(55,   symbol)                   # Symbol
    msg.append_pair(60,   format_epoch_time(now))   # Transaction Timestamp(now)

    return now, msg.encode()

def getMsgRFQ(symbol: str, price: float, quantity: float, apikey: str, seqnum: int = 2):

    msg = sfx.FixMessage()
    now = int(time.time())

    assert apikey is not None, "Error - API KEY must not be empty or None"
    assert price is not None, "Error - price must not be empty value or None"
    assert price > 0.00, "Error - price must be greater than zero"

    # Header
    msg.append_pair(8,    "FIX.4.4", True)
    msg.append_pair(35,   "R", True)
    msg.append_pair(34,   seqnum, True)
    msg.append_pair(49,   apikey, True)
    msg.append_pair(52,   format_epoch_time(now), True)
    msg.append_pair(56,   "PT-OE", True)

    # Body
    msg.append_pair(11,   now)
    msg.append_pair(131,  now)
    msg.append_pair(146,  2)
    msg.append_pair(55,   symbol)
    msg.append_pair(55,   "SOL-USD")

    #msg.append_pair(38,  quantity)
    #msg.append_pair(40,  2)
    #msg.append_pair(44,  price)
    #msg.append_pair(54,  1)
    #msg.append_pair(58,  "Please provide quotes for SOL-USD and ETH-USD")
    #msg.append_pair(60,  format_epoch_time(now))

    return now, msg.encode()

def getMsgCancel(orderID: str, cancelOrderID:int, symbol: str, apikey: str, seqnum: int, side: int=1):

    assert orderID is not None, "Error - orderId must not be empty or None"

    msg = sfx.FixMessage()
    now = int(time.time())

    # Header
    msg.append_pair(8,   "FIX.4.4", True)
    msg.append_pair(35,  "F", True)
    msg.append_pair(34,  seqnum, True)
    msg.append_pair(49,  apikey, True)
    msg.append_pair(52,  format_epoch_time(now), True)
    msg.append_pair(56,  "PT-OE", True)

    # Body
    msg.append_pair(11,  cancelOrderID)          # <field name='ClOrdID' required='Y' />
    msg.append_pair(41,  orderID)                # <field name='OrigClOrdID' required='Y' />
    msg.append_pair(54,  side)                      # <field name='Side' required='Y' />
    msg.append_pair(55,  symbol)                 # <component name='Instrument' required='Y' />
    msg.append_pair(60,  format_epoch_time(now)) # <field name='TransactTime' required='Y' />

    return now, msg.encode()

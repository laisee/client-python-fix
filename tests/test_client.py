from unittest import TestCase
import os
import pytest

from messages import (
    checkMsg,
    checkLogonMsg,
    getMsgCancel,
    getMsgLogon,
    getMsgNewOrder,
    getMsgRFQ,
)
from utils import generateJWT

APIKEY = "DUMMMY"
MSG_LOGON = b"8=FIX.4.2|9=112|35=A|34=1|49=CLIENT|52=20240729-14:35:00.000|56=SERVER|98=0|108=30|10=072|"
SENDER = "CLIENT"
RECEIVER = "SERVER"
SYMBOL = "ETH"
PRICE = 1.3465345
QUANTITY = "2.888"
ORDERID = "orderId12342342"
SEQNUM = 3


class BasicMsgTest(TestCase):
    def test_checkMsg(self):
        status = checkMsg(MSG_LOGON, SENDER, RECEIVER)
        assert status is True

    def test_checkLogonMsg(self):
        status, msg = checkLogonMsg(MSG_LOGON)
        assert status is True  # no error found in message
        assert len(msg) == 0  # no error means no error message

    def test_getMsgLOGON(self):
        assert getMsgLogon is not None
        with pytest.raises(ValueError, match="API_SECRET"):
            msg = getMsgLogon(APIKEY)
            assert msg is not None

    def test_getMsgNewOrder(self):
        assert getMsgNewOrder is not None
        msg = getMsgNewOrder(
            symbol=SYMBOL, price=PRICE, quantity=QUANTITY, apikey=APIKEY
        )
        assert msg is not None
        assert len(msg) > 0
        msg_str = msg[1].decode("utf-8") if isinstance(msg, tuple) else msg.decode("utf-8")
        assert "35=D" in msg_str

    def test_generateJWT_requires_env(self):
        os.environ.pop("API_SECRET", None)
        os.environ.pop("API_URI", None)
        with pytest.raises(ValueError):
            generateJWT(APIKEY, 0)

    def test_getMsgRFQ(self):
        assert getMsgRFQ is not None
        msg = getMsgRFQ(symbol=SYMBOL, price=PRICE, quantity=QUANTITY, apikey=APIKEY)
        assert msg is not None

    def test_getMsgCancel(self):
        cancelOrderID = "CNCLwe53463456"
        assert getMsgCancel is not None
        msg = getMsgCancel(
            orderID="1213241234",
            cancelOrderID=cancelOrderID,
            symbol=SYMBOL,
            apikey=APIKEY,
            seqnum=SEQNUM,
        )
        assert msg is not None


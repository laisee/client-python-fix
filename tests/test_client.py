from unittest import TestCase

from messages import checkMsg, getMsgLogon, getMsgNewOrder, getMsgRFQ, getMsgCancel

class DummyTest(TestCase):
    def test_checkMsg(self):
        msg = checkMsg(b"msg", None, None)
        assert msg is not None

    def test_getMsgLOGON(self):
        assert getMsgLogon is not None

    def test_getMsgNewOrder(self):
        assert getMsgNewOrder is not None

    def test_getMsgRFQ(self):
        assert getMsgRFQ is not None

    def test_getMsgCancel(self):
        assert getMsgCancel is not None

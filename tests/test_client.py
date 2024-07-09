from unittest import TestCase

from messages import checkMsg, getMsgLOGON, getMsgNewOrder, getMsgRFQ, getMsgCancel

class DummyTest(TestCase):
    def test_always_passes(self):
        self.assertTrue(True)

    def test_always_fails(self):
        self.assertFalse(False)

    def test_checkMsg(self):
        msg = checkMsg(b"msg", None, None)
        assert msg is not None

    def test_getMsgLOGON(self):
        assert getMsgLOGON is not None

    def test_getMsgNewOrder(self):
        assert getMsgNewOrder is not None

    def test_getMsgRFQ(self):
        assert getMsgRFQ is not None

    def test_getMsgCancel(self):
        assert getMsgCancel is not None

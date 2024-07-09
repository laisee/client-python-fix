from unittest import TestCase

from client import *


class DummyTest(TestCase):
    def test_always_passes(self):
        self.assertTrue(True)

    def test_always_fails(self):
        self.assertFalse(False)

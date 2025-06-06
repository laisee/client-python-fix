import os
from datetime import datetime, UTC
import pytest

import utils
import messages


def decode_fix(msg: bytes) -> dict[str, str]:
    string = msg.decode('utf-8').replace('\x01', '|')
    return utils.get_attrs(string)


def test_get_attrs_and_get_attr():
    msg = "8=FIX.4.4|35=D|49=CLIENT|56=PT-OE|11=123|"
    attrs = utils.get_attrs(msg)
    assert attrs["8"] == "FIX.4.4"
    assert utils.get_attr(msg, "35") == "D"
    assert utils.get_attr(msg, "99") is None


def test_format_epoch_time():
    assert utils.format_epoch_time(0) == "19700101-00:00:00.000"


def test_get_log_filename(monkeypatch):
    fixed = datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)

    class DummyDatetime:
        @classmethod
        def utcnow(cls):
            return fixed

    monkeypatch.setattr(utils, "datetime", DummyDatetime)
    filename = utils.get_log_filename("prefix")
    assert filename == "prefix_20240102_030405.log"


def test_generate_jwt_success(monkeypatch):
    os.environ["API_SECRET"] = "secret"
    os.environ["API_URI"] = "uri"
    monkeypatch.setattr(utils.jwt, "encode", lambda p, k, algorithm=None: "TOKEN")
    assert utils.generateJWT("api", 123) == "TOKEN"


def test_getMsgHeartbeat_and_errors():
    with pytest.raises(AssertionError):
        messages.getMsgHeartbeat(None, 3)
    with pytest.raises(AssertionError):
        messages.getMsgHeartbeat("api", 2)

    msg = messages.getMsgHeartbeat("api", 3)
    attrs = decode_fix(msg)
    assert attrs["35"] == "0"
    assert attrs["34"] == "3"
    assert attrs["49"] == "api"


def test_getMsgLogon(monkeypatch):
    monkeypatch.setattr(messages, "generateJWT", lambda a, n: "TOK")
    msg = messages.getMsgLogon("api")
    attrs = decode_fix(msg)
    assert attrs["35"] == "A"
    assert attrs["49"] == "api"
    assert attrs["554"] == "TOK"


def test_translateFix_cases():
    assert messages.translateFix("35", "D") == "New Order - Single"
    assert messages.translateFix("39", "4") == "Cancelled"
    assert "UNKNOWN Fix key" in messages.translateFix("35", "Z")
    assert "UNKNOWN Fix field" in messages.translateFix("99", "1")

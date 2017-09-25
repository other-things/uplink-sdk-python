import pytest

from uplink import *
from uplink.utils import *


def test_ecdsa():
    (pk, sk) = ecdsa_new()
    msg = "Hello Ledger".encode(encoding='UTF-8')
    sig = ecdsa_sign(sk, msg)
    assert ecdsa_verify(pk, sig, msg)

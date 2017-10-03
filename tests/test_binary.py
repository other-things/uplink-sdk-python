import os
import os.path

import hexdump
from uplink import *
from uplink.utils import *
import pytest

from . import reference

golden_output = "tests/golden/"


def golden_binary(fname, tx):
    stream = hexdump.hexdump(tx.to_binary(), result='return')
    if os.path.exists(golden_output + fname):
        with open(golden_output + fname, 'r') as fd:
            expected = fd.read()
            assert expected == stream
    else:
        with open(golden_output + fname, 'w+') as fd:
            fd.write(stream)
    return stream


def test_tx_transfer():
    tx = reference.testTransfer
    golden_binary("tx_transfer.bin", tx)


def test_create_account():
    tx = reference.testCreateAccount
    golden_binary("tx_create_account.bin", tx)


def test_revoke_account():
    tx = reference.testRevokeAccount
    golden_binary("tx_revoke_account.bin", tx)


def test_create_contract():
    tx = reference.testCreateContract
    golden_binary("tx_create_contract.bin", tx)


def test_create_asset():
    tx = reference.testCreateAsset
    golden_binary("tx_create_asset.bin", tx)


@pytest.mark.parametrize(("arg"), reference.test_args)
def test_call(arg):
    tx = reference.testCall([arg])

    golden_binary("tx_call_{}.bin".format(type(arg).__name__), tx)


@pytest.mark.parametrize(("arg_count"), range(0, 5))
def test_call_arg_length(arg_count):
    tx = reference.testCall([VInt(1)] * arg_count)
    golden_binary("tx_call_{}_args.bin".format(arg_count), tx)


def test_bind():
    tx = reference.testBind
    golden_binary("tx_bind.bin", tx)

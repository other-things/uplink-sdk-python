import os
import os.path

from uplink import *
from uplink.utils import *
import pytest
import reference

golden_output = "tests/golden/"


def golden_signature(fname, tx):
    (r, s) = tx.sign(reference.skey, k=reference.nonce)
    o1 = "r = " + str(r) + "\n"
    o2 = "s = " + str(s) + "\n"

    if os.path.exists(golden_output + fname):
        with open(golden_output + fname, 'r') as fd:
            e1 = fd.readline()
            e2 = fd.readline()
            assert e1 == o1
            assert e2 == o2
    else:
        with open(golden_output + fname, 'w+') as fd:
            fd.write(o1)
            fd.write(o2)
    return (r, s)


def test_tx_transfer():
    tx = reference.testTransfer
    golden_signature("tx_transfer.sig", tx)


def test_create_account():
    tx = reference.testCreateAccount
    golden_signature("tx_create_account.sig", tx)


def test_revoke_account():
    tx = reference.testRevokeAccount
    golden_signature("tx_revoke_account.sig", tx)


def test_create_contract():
    tx = reference.testCreateContract
    golden_signature("tx_create_contract.sig", tx)


@pytest.mark.parametrize(("arg"), reference.test_args)
def test_call(arg):
    tx = reference.testCall([arg])

    golden_signature("tx_call_{}.sig".format(type(arg).__name__), tx)


@pytest.mark.parametrize(("arg_count"), range(0,5))
def test_call_arg_length(arg_count):

    tx = reference.testCall([VInt(1)] * arg_count)
    golden_signature("tx_call_{}_args.sig".format(arg_count), tx)


def test_create_asset():
    tx = reference.testCreateAsset
    golden_signature("tx_create_asset.sig", tx)

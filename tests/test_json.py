import os
import os.path

from uplink import *

import codecs
import reference
import json

golden_output = "tests/golden/"
import pytest


def golden_json(fname, tx):
    if os.path.exists(golden_output + fname):
        with open(golden_output + fname, 'r') as fd:
            expected = fd.read()
            assert json.loads(expected) == tx.to_dict()
    else:
        with open(golden_output + fname, 'w+') as fd:
            fd.write(tx.to_json(indent=4))
    return tx


# ------------------------------------------------------------------------
# Headers
# ------------------------------------------------------------------------


def test_transfer_hdr():
    tx = reference.testTransfer
    golden_json('tx_transfer_hdr.json', tx)


def test_create_account_hdr():
    tx = reference.testCreateAccount
    golden_json('tx_create_account_hdr.json', tx)


def test_create_asset_hdr():
    tx = reference.testCreateAsset
    golden_json('tx_create_asset_hdr.json', tx)


def test_create_contract_hdr():
    tx = reference.testCreateContract
    golden_json('tx_create_contract_hdr.json', tx)


def test_revoke_account_hdr():
    tx = reference.testRevokeAccount
    golden_json('tx_revoke_account_hdr.json', tx)


@pytest.mark.parametrize(("args"), reference.test_args)
def test_call(args):
    tx = reference.testCall(args)

    golden_json("tx_call_hdr_{}.json".format(type(args).__name__), tx)


def test_bind_hdr():
    tx = reference.testBind
    golden_json('tx_bind_hdr.json', tx)


# ------------------------------------------------------------------------
# Full Transactions
# ------------------------------------------------------------------------


def test_transfer():
    tx = reference.testTx(TxAsset, CreateAsset, reference.testTransfer)
    golden_json('tx_transfer.json', tx)


def test_create_account():
    tx = reference.testTx(
        TxAccount, CreateAccount, reference.testCreateAccount)
    golden_json('tx_create_account.json', tx)


def test_create_asset():
    tx = reference.testTx(TxAsset, CreateAsset, reference.testCreateAsset)
    golden_json('tx_create_asset.json', tx)


def test_create_contract():
    tx = reference.testTx(
        TxContract, CreateContract, reference.testCreateContract)
    golden_json('tx_create_contract.json', tx)


def test_revoke():
    tx = reference.testTx(TxAccount, RevokeAccount, reference.testRevokeAccount)
    golden_json('tx_revoke.json', tx)


@pytest.mark.parametrize(("arg"), reference.test_args)
def test_call(arg):

    tx = reference.testTx(TxContract, Call, reference.testCall([arg]))
    golden_json("tx_call_{}.json".format(type(arg).__name__), tx)


@pytest.mark.parametrize(("arg_count"), range(0,5))
def test_call_arg_length(arg_count):

    tx = reference.testTx(TxContract, Call, reference.testCall([VInt(1)] * arg_count))
    golden_json("tx_call_{}_args.json".format(arg_count), tx)


def test_bind():
    tx = reference.testTx(TxAsset, Bind, reference.testBind)
    golden_json('tx_bind.json', tx)

from ecdsa.keys import *
from ecdsa.ecdsa import *
from ecdsa.curves import *
from uplink import *

from uplink.fixtures import *


def test_create_account(alice_account, bob_account):
    # extra checks belong here
    pass  # if the fixtures ran successfully then the accounts were created successfully


def test_create_asset(gold_asset, silver_asset):
    # extra checks belong here
    pass  # if the fixture ran successfully then the assets were created successfully


def test_transfer_assets(rpc, alice_account, bob_account, gold_asset):
    # transfer alice gold asset supply to alice holdings
    t1 = rpc.uplink_circulate_asset(private_key=alice_account.private_key,
                                    from_address=alice_account.address,
                                    amount=500,
                                    asset_address=gold_asset.address)

    assert is_rpc_ok(t1)
    # transfer alice holdings to bob holdings
    t2 = rpc.uplink_transfer_asset(private_key=alice_account.private_key,
                                   from_address=alice_account.address,
                                   to_address=bob_account.address,
                                   balance=250,
                                   asset_address=gold_asset.address)

    assert is_rpc_ok(t2)
    # transfer bob holdings back to alice holdings
    t3 = rpc.uplink_transfer_asset(private_key=bob_account.private_key,
                                   from_address=bob_account.address,
                                   to_address=alice_account.address,
                                   balance=50,
                                   asset_address=gold_asset.address)
    assert is_rpc_ok(t3)


def test_revoke_account(rpc, per_test_account):
    result = rpc.uplink_revoke_account(private_key=per_test_account.private_key, from_address=per_test_account.address,
                                       account_addr=per_test_account.address)
    assert is_rpc_ok(result)


def test_call_contract(rpc, example_contract, alice_account):
    result = rpc.uplink_call_contract(private_key=alice_account.private_key, from_address=alice_account.address,
                                      contract_addr=example_contract.address,
                                      method='setX',
                                      args=[VInt(42)])
    assert is_rpc_ok(result)
    result1 = rpc.uplink_call_contract(private_key=alice_account.private_key, from_address=alice_account.address,
                                       contract_addr=example_contract.address,
                                       method='getX',
                                       args=[])
    assert is_rpc_ok(result1)


def test_oracle_contract(rpc, oracle_contract, alice_account, contract_using_oracle_contract):
    result = rpc.uplink_call_contract(private_key=alice_account.private_key, from_address=alice_account.address,
                                      contract_addr=oracle_contract.address,
                                      method='set',
                                      args=[VFloat(2)])
    assert is_rpc_ok(result)

    result = rpc.uplink_call_contract(private_key=alice_account.private_key, from_address=alice_account.address,
                                      contract_addr=contract_using_oracle_contract.address,
                                      method='setX',
                                      args=[VFloat(5.3), VContract(oracle_contract.address)])

    wait_until(lambda: rpc.uplink_get_contract(contract_using_oracle_contract.address).storage['x']['contents'] == 10.6)

    assert is_rpc_ok(result)


@pytest.mark.parametrize(("method_name", "arg"), [
    ("fn_int", VInt(404)),
    ("fn_float", VFloat(2)),
    ("fn_bool", VBool(False)),
    ("fn_msg", VMsg("Hello World")),
    ("fn_account", VAccount(testAddr)),
    ("fn_asset", VAsset(testAddr)),
    ("fn_contract", VContract(testAddr)),
    ("fn_datetime", VDateTime(datetime.datetime.now())),
    ("fn_void", VVoid)
])
def test_all_args_contract(rpc, all_args_contract, alice_account, method_name, arg):
    result = rpc.uplink_call_contract(private_key=alice_account.private_key, from_address=alice_account.address,
                                      contract_addr=all_args_contract.address,
                                      method=method_name,
                                      args=[arg])
    assert is_rpc_ok(result)


def test_create_contract(rpc, example_contract):
    # extra checks belong here
    pass  # if the fixtures ran successfully then the contract was created successfully


def test_get_transactions(rpc, alice_account):
    result = rpc.uplink_transactions(1)
    assert (len(result) > 0)


def test_peers(rpc):
    peers = rpc.uplink_peers()
    assert (len(peers) > 0)


def test_validators(rpc):
    validators = rpc.uplink_validators()
    assert (len(validators) > 0)


def test_get_account(rpc, alice_account):
    result = rpc.uplink_get_account(alice_account.address)
    assert result


def test_accounts(rpc, alice_account):
    result = rpc.uplink_accounts()
    assert (len(result) > 0)


def test_contracts(rpc, example_contract):
    result = rpc.uplink_contracts()
    assert (len(result) > 0)


def test_get_contract(rpc, example_contract):
    result = rpc.uplink_get_contract(example_contract.address)
    assert result


def test_get_contract_callable(rpc, all_args_contract):
    result = rpc.uplink_get_contract_callable(all_args_contract.address)
    assert result == {u'fn_void': [[u'a', u'void']], u'fn_account': [[u'a', u'account']],
                      u'fn_asset': [[u'a', u'asset']], u'fn_contract': [[u'e', u'contract']],
                      u'fn_int': [[u'a', u'int']], u'fn_msg': [[u'c', u'msg']], u'fn_float': [[u'b', u'float']],
                      u'never_called': [[u'a', u'void']], u'fn_bool': [[u'x', u'bool']],
                      u'fn_datetime': [[u'e', u'datetime']]}


def test_assets(rpc):
    result = rpc.uplink_assets()
    assert (len(result) > 0)


def test_get_asset(rpc, gold_asset):
    result = rpc.uplink_get_asset(gold_asset.address)
    assert result


def test_version(rpc):
    version_info = rpc.uplink_version()
    assert 'commit' in version_info
    assert 'dirty' in version_info
    assert 'version' in version_info
    assert 'branch' in version_info

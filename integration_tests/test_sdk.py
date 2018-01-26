from ecdsa.keys import *
from ecdsa.ecdsa import *
from ecdsa.curves import *
from uplink import *

from uplink.fixtures import *
from uplink.fixtures import is_rpc_ok, wait_until


def test_create_account(alice_account, bob_account):
    # extra checks belong here

    # if the fixtures ran successfully then the
    # accounts were created successfully
    pass


def test_create_asset(gold_asset, silver_asset):
    # extra checks belong here

    # if the fixture ran successfully then the
    # assets were created successfully
    pass


def test_transfer_asset(rpc, alice_account, bob_account, gold_asset):
    # Shorter alias for querying asset
    def get_asset():
        return rpc.uplink_get_asset(gold_asset.address)

    # transfer alice gold asset supply to alice holdings
    t1 = rpc.uplink_circulate_asset(private_key=alice_account.private_key,
                                    from_address=alice_account.address,
                                    amount=500,
                                    asset_address=gold_asset.address)
    assert is_rpc_ok(t1)
    wait_until(lambda: get_asset().supply == (gold_asset.supply - 500))
    wait_until(lambda: get_asset().holdings[alice_account.address] == 500)

    # transfer alice holdings to bob holdings
    t2 = rpc.uplink_transfer_asset(private_key=alice_account.private_key,
                                   from_address=alice_account.address,
                                   to_address=bob_account.address,
                                   balance=250,
                                   asset_address=gold_asset.address)
    assert is_rpc_ok(t2)
    wait_until(lambda: get_asset().holdings[alice_account.address] == 250)
    wait_until(lambda: get_asset().holdings[bob_account.address] == 250)

    # transfer bob holdings back to alice holdings
    t3 = rpc.uplink_transfer_asset(private_key=bob_account.private_key,
                                   from_address=bob_account.address,
                                   to_address=alice_account.address,
                                   balance=50,
                                   asset_address=gold_asset.address)
    assert is_rpc_ok(t3)
    wait_until(lambda: get_asset().holdings[bob_account.address] == 200)
    wait_until(lambda: get_asset().holdings[alice_account.address] == 300)


def test_revoke_account(rpc, per_test_account):
    result = rpc.uplink_revoke_account(private_key=per_test_account.private_key,
                                       from_address=per_test_account.address,
                                       account_addr=per_test_account.address)
    assert is_rpc_ok(result)

    def check_revoked_account():
        try:
            rpc.uplink_get_account(per_test_account.address)
            return False
        except UplinkJsonRpcError as e:
            return e.contents["errorMessage"] == "NotFound"

    wait_until(lambda: check_revoked_account)


def test_call_contract(rpc, example_contract, alice_account):
    def get_contract():
        """ Shorter alias for contract query """
        return rpc.uplink_get_contract(example_contract.address)

    # Set 'x' value to 42
    result = rpc.uplink_call_contract(private_key=alice_account.private_key,
                                      from_address=alice_account.address,
                                      contract_addr=example_contract.address,
                                      method='setX',
                                      args=[VInt(42)])

    assert is_rpc_ok(result)

    # Wait until 'x' = 42
    wait_until(lambda: get_contract().storage["x"]["contents"] == 42)

    # Terminate the contract
    result1 = rpc.uplink_call_contract(private_key=alice_account.private_key,
                                       from_address=alice_account.address,
                                       contract_addr=example_contract.address,
                                       method='getX',
                                       args=[])
    assert is_rpc_ok(result1)
    wait_until(lambda: get_contract().state == "terminal")


def test_oracle_contract(rpc, oracle_contract, alice_account, contract_using_oracle_contract):
    result = rpc.uplink_call_contract(private_key=alice_account.private_key,
                                      from_address=alice_account.address,
                                      contract_addr=oracle_contract.address,
                                      method='set',
                                      args=[VFloat(2)])
    assert is_rpc_ok(result)

    result = rpc.uplink_call_contract(private_key=alice_account.private_key,
                                      from_address=alice_account.address,
                                      contract_addr=contract_using_oracle_contract.address,
                                      method='setX',
                                      args=[VFloat(5.3), VContract(oracle_contract.address)])

    assert is_rpc_ok(result)
    wait_until(lambda: rpc.uplink_get_contract(
        contract_using_oracle_contract.address).storage['x']['contents'] == 10.6)


def test_circulate_and_transfer(rpc, alice_account, bob_account, alice_circulate_transfer_asset, contract_circulate_transfer):
    # Shorter alias for querying asset
    def get_asset():
        return rpc.uplink_get_asset(alice_circulate_transfer_asset.address)

    # Circulate 5000/10000 to alice (asset issuer)
    result1 = rpc.uplink_call_contract(private_key=alice_account.private_key,
                                       from_address=alice_account.address,
                                       contract_addr=contract_circulate_transfer.address,
                                       method='circulate1',
                                       args=[VAsset(alice_circulate_transfer_asset.address), VInt(5000)])
    assert is_rpc_ok(result1)

    # Transfer 5000 from alice to bob
    result2 = rpc.uplink_call_contract(private_key=alice_account.private_key,
                                       from_address=alice_account.address,
                                       contract_addr=contract_circulate_transfer.address,
                                       method='transfer1',
                                       args=[VAsset(alice_circulate_transfer_asset.address),
                                             VAccount(alice_account.address),
                                             VAccount(bob_account.address),
                                             VInt(5000)])
    assert is_rpc_ok(result2)

    # Circulate 5000/5000 to alice (0 supply left)
    result3 = rpc.uplink_call_contract(private_key=alice_account.private_key,
                                       from_address=alice_account.address,
                                       contract_addr=contract_circulate_transfer.address,
                                       method='circulate2',
                                       args=[VAsset(alice_circulate_transfer_asset.address), VInt(5000)])
    assert is_rpc_ok(result3)

    # Transfer 5000 from alice to bob (alice should have 0 holdings)
    result4 = rpc.uplink_call_contract(private_key=alice_account.private_key,
                                       from_address=alice_account.address,
                                       contract_addr=contract_circulate_transfer.address,
                                       method='transfer2',
                                       args=[VAsset(alice_circulate_transfer_asset.address),
                                             VAccount(alice_account.address),
                                             VAccount(bob_account.address),
                                             VInt(5000)])
    assert is_rpc_ok(result4)

    # entire asset supply should be circulated by 3rd transaction
    wait_until(lambda: get_asset().supply == 0)

    circ_tran_asset = get_asset()
    assert (circ_tran_asset.supply == 0)
    assert (len(circ_tran_asset.holdings) == 1)
    assert (circ_tran_asset.holdings[bob_account.address] == 10000)


@pytest.mark.parametrize(("method_name", "var_name", "arg"), [
    ("fn_int", "a", VInt(404)),
    ("fn_float", "b", VFloat(2.123456789)),
    # ("fn_fixed5", "c", VFixed(6.54321,5)), XXX not implemented yet
    ("fn_bool", "d", VBool(False)),
    ("fn_msg", "e", VMsg("Hello World")),
    ("fn_account", "f", VAccount(testAddr)),
    ("fn_asset", "g", VAsset(testAddr)),
    ("fn_contract", "h", VContract(testAddr)),
    ("fn_datetime", "i", VDateTime(datetime.datetime.now()))
])
def test_all_args_contract(rpc, all_args_contract, alice_account, method_name, var_name, arg):
    result = rpc.uplink_call_contract(private_key=alice_account.private_key, from_address=alice_account.address,
                                      contract_addr=all_args_contract.address,
                                      method=method_name,
                                      args=[arg])
    assert is_rpc_ok(result)

    def get_contract_storage():
        storage = rpc.uplink_get_contract(all_args_contract.address).storage
        print(storage)
        return storage

    # Intially, all top level values in the all_args_contract are undefined. We
    # set them by making a function call, and resultingly they should not be
    # undefined.
    wait_until(lambda: get_contract_storage()[
               var_name]["contents"] is not None)


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
    assert result == {u'fn_int': [[u'a_', u'int']],
                      u'fn_float': [[u'b_', u'float']],
                      # XXX not implemented yet
                      u'fn_fixed5': [[u'c_', u'fixed5']],
                      u'fn_bool': [[u'd_', u'bool']],
                      u'fn_msg': [[u'e_', u'msg']],
                      u'fn_account': [[u'f_', u'account']],
                      u'fn_asset': [[u'g_', u'asset']],
                      u'fn_contract': [[u'h_', u'contract']],
                      u'fn_datetime': [[u'i_', u'datetime']],
                      u'never_called': []
                      }


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


def test_query(rpc, alice_account):
    q1 = "QUERY contracts WHERE state = 'initial';"
    q2 = "QUERY assets WHERE assetType = 'Discrete';"
    q3 = "QUERY accounts WHERE address = '{}';".format(alice_account.address)
    q4 = "QUERY transactions WHERE tx_type = 'CreateAccount';"

    a1 = rpc.uplink_query(q1)
    a2 = rpc.uplink_query(q2)
    a3 = rpc.uplink_query(q3)
    a4 = rpc.uplink_query(q4)

    assert (len(a1) >= 0)
    assert (len(a2) >= 0)
    assert (len(a3) >= 0)
    assert (len(a4) >= 0)

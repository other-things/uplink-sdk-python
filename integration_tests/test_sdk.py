from ecdsa.keys import *
from ecdsa.ecdsa import *
from ecdsa.curves import *
from uplink import *

from uplink.fixtures import *
from uplink.fixtures import is_rpc_ok, wait_until

from uplink.version import __version__


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

def test_create_asset_fractional(platinum_asset):
    # extra checks belong here

    # if the fixture ran successfully then the
    # assets were created successfully
    pass

def test_transfer_asset(rpc, alice_account, bob_account, gold_asset):
    # Shorter alias for querying asset
    def get_asset():
        return rpc.uplink_get_asset(gold_asset.address)

    # transfer alice gold asset supply to alice holdings
    tx_hash_0 = rpc.uplink_circulate_asset(private_key=alice_account.private_key,
                                           from_address=alice_account.address,
                                           amount=500,
                                           asset_address=gold_asset.address)
    wait_until_tx_accepted(rpc, tx_hash_0)
    circulated_asset = get_asset()
    # Assert the circulation worked
    assert circulated_asset.supply == gold_asset.supply - 500
    assert circulated_asset.holdings[alice_account.address] == 500

    # transfer alice holdings to bob holdings
    tx_hash_1 = rpc.uplink_transfer_asset(private_key=alice_account.private_key,
                                          from_address=alice_account.address,
                                          to_address=bob_account.address,
                                          balance=250,
                                          asset_address=gold_asset.address)
    wait_until_tx_accepted(rpc, tx_hash_1)
    transferred_asset_1 = get_asset()
    # Assert the transfer worked
    assert transferred_asset_1.holdings[alice_account.address] == 250
    assert transferred_asset_1.holdings[bob_account.address] == 250

    # transfer bob holdings back to alice holdings
    tx_hash_2 = rpc.uplink_transfer_asset(private_key=bob_account.private_key,
                                          from_address=bob_account.address,
                                          to_address=alice_account.address,
                                          balance=50,
                                          asset_address=gold_asset.address)

    wait_until_tx_accepted(rpc, tx_hash_2)
    transferred_asset_2 = get_asset()
    # Assert the transfer worked
    assert transferred_asset_2.holdings[bob_account.address] == 200
    assert transferred_asset_2.holdings[alice_account.address] == 300


def test_revoke_account(rpc, per_test_account):
    tx_hash = rpc.uplink_revoke_account(private_key=per_test_account.private_key,
                                        from_address=per_test_account.address,
                                        account_addr=per_test_account.address)
    wait_until_tx_accepted(rpc, tx_hash)

    def check_revoked_account():
        try:
            rpc.uplink_get_account(per_test_account.address)
            return False
        except UplinkJsonRpcError as e:
            return True

    assert check_revoked_account()


def test_call_contract(rpc, example_contract, alice_account):
    def get_contract():
        """ Shorter alias for contract query """
        return rpc.uplink_get_contract(example_contract.address)

    # Set 'x' value to 42
    txhash = rpc.uplink_call_contract(private_key=alice_account.private_key,
                                      from_address=alice_account.address,
                                      contract_addr=example_contract.address,
                                      method='setX',
                                      args=[VInt(42)])
    # Check if 'x' = 42
    wait_until_tx_accepted(rpc, txhash)
    assert get_contract().storage["x"]["contents"] == 42

    # Terminate the contract
    txhash1 = rpc.uplink_call_contract(private_key=alice_account.private_key,
                                       from_address=alice_account.address,
                                       contract_addr=example_contract.address,
                                       method='end',
                                       args=[])
    # Check if contract is in terminal state
    wait_until_tx_accepted(rpc, txhash1)
    assert get_contract().state == "terminal"


def test_oracle_contract(rpc, oracle_contract, alice_account, contract_using_oracle_contract):
    def get_contract(address):
        """ Shorter alias for contract query """
        return rpc.uplink_get_contract(address)

    txhash = rpc.uplink_call_contract(private_key=alice_account.private_key,
                                      from_address=alice_account.address,
                                      contract_addr=oracle_contract.address,
                                      method='set',
                                      args=[VFloat(2)])
    wait_until_tx_accepted(rpc, txhash)
    assert get_contract(oracle_contract.address).storage["value"]["contents"] == 2.0

    txhash = rpc.uplink_call_contract(private_key=alice_account.private_key,
                                      from_address=alice_account.address,
                                      contract_addr=contract_using_oracle_contract.address,
                                      method='setX',
                                      args=[VFloat(5.3), VContract(oracle_contract.address)])

    wait_until_tx_accepted(rpc, txhash)
    assert get_contract(contract_using_oracle_contract.address).storage['x']['contents'] == 10.6

@pytest.mark.parametrize(("asset_name", "supply", "asset_type_name", "precision", "transfer_val"), [
    ("circ_tran_discrete", 1000000, "Discrete", None, VInt(500000)),
    ("circ_tran_binary", 2, "Binary", None, VBool(True)),
    ("circ_tran_frac1", 1000000, "Fractional", 1, VFixed(Decimal("50000.0"), 1)),
    ("circ_tran_frac2", 1000000, "Fractional", 2, VFixed(Decimal("5000.00"), 2)),
    ("circ_tran_frac3", 1000000, "Fractional", 3, VFixed(Decimal("500.000"), 3)),
    ("circ_tran_frac4", 1000000, "Fractional", 4, VFixed(Decimal("50.0000"), 4)),
    ("circ_tran_frac5", 1000000, "Fractional", 5, VFixed(Decimal("5.00000"), 5)),
    ("circ_tran_frac6", 1000000, "Fractional", 6, VFixed(Decimal(".500000"), 6))
])
def test_circulate_and_transfer(rpc, alice_account, bob_account, asset_gen,
                                circulate_transfer_contract_gen, asset_name,
                                supply, asset_type_name, precision,
                                transfer_val):

    circ_tran_asset = asset_gen(asset_name, alice_account, supply,
                                asset_type_name, precision)

    circ_tran_contract = circulate_transfer_contract_gen(asset_type_name, precision)

    def get_transfer_val_as_int():
        type_name = type(transfer_val).__name__
        if type_name == "VInt":
            return transfer_val[0]
        elif type_name == "VBool":
            return int(transfer_val[0])
        elif type_name == "VFixed":
            return int(float(transfer_val[0]) * 10.0**precision)
        else:
            raise TypeError

    transfer_val_int = get_transfer_val_as_int()

    # Shorter alias for querying asset
    def get_asset():
        return rpc.uplink_get_asset(circ_tran_asset.address)

    # Circulate half of supply to alice (asset issuer)
    txhash1 = rpc.uplink_call_contract(private_key=alice_account.private_key,
                                       from_address=alice_account.address,
                                       contract_addr=circ_tran_contract.address,
                                       method='circulate1',
                                       args=[VAsset(circ_tran_asset.address),
                                             transfer_val])
    wait_until_tx_accepted(rpc, txhash1)
    circulated1_asset = get_asset()
    assert circulated1_asset.supply == transfer_val_int
    assert circulated1_asset.holdings[alice_account.address] == transfer_val_int

    # Transfer all holdings from alice to bob
    txhash2 = rpc.uplink_call_contract(private_key=alice_account.private_key,
                                       from_address=alice_account.address,
                                       contract_addr=circ_tran_contract.address,
                                       method='transfer1',
                                       args=[VAsset(circ_tran_asset.address),
                                             VAccount(alice_account.address),
                                             VAccount(bob_account.address),
                                             transfer_val])
    wait_until_tx_accepted(rpc, txhash2)
    transfer1_asset= get_asset()
    assert transfer1_asset.holdings[bob_account.address] == transfer_val_int
    assert (len(transfer1_asset.holdings) == 1)

    # Circulate remaining supply to alice (0 supply left)
    txhash3 = rpc.uplink_call_contract(private_key=alice_account.private_key,
                                       from_address=alice_account.address,
                                       contract_addr=circ_tran_contract.address,
                                       method='circulate2',
                                       args=[VAsset(circ_tran_asset.address),
                                             transfer_val])
    
    wait_until_tx_accepted(rpc, txhash3)
    # entire asset supply should be circulated now
    circulated2_asset = get_asset()
    assert circulated2_asset.supply == 0
    assert circulated2_asset.holdings[alice_account.address] == transfer_val_int

    # Transfer all from alice to bob (alice should have 0 holdings)
    txhash4 = rpc.uplink_call_contract(private_key=alice_account.private_key,
                                       from_address=alice_account.address,
                                       contract_addr=circ_tran_contract.address,
                                       method='transfer2',
                                       args=[VAsset(circ_tran_asset.address),
                                             VAccount(alice_account.address),
                                             VAccount(bob_account.address),
                                             transfer_val])
    wait_until_tx_accepted(rpc, txhash4)
    # Bob should have all the holdings
    transfer2_asset = get_asset()
    assert transfer2_asset.holdings[bob_account.address] == supply
    assert (len(transfer2_asset.holdings) == 1)


@pytest.mark.parametrize(("asset_name", "supply", "asset_type_name", "precision", "transfer_val"), [
    ("sim_circ_tran_discrete", 1000000, "Discrete", None, VInt(500000)),
    ("sim_circ_tran_binary", 2, "Binary", None, VBool(True)),
    ("sim_circ_tran_frac1", 1000000, "Fractional", 1, VFixed(Decimal("50000.0"), 1)),
    ("sim_circ_tran_frac2", 1000000, "Fractional", 2, VFixed(Decimal("5000.00"), 2)),
    ("sim_circ_tran_frac3", 1000000, "Fractional", 3, VFixed(Decimal("500.000"), 3)),
    ("sim_circ_tran_frac4", 1000000, "Fractional", 4, VFixed(Decimal("50.0000"), 4)),
    ("sim_circ_tran_frac5", 1000000, "Fractional", 5, VFixed(Decimal("5.00000"), 5)),
    ("sim_circ_tran_frac6", 1000000, "Fractional", 6, VFixed(Decimal(".500000"), 6))
])
def test_circulate_and_transfer_simulation(rpc, alice_account, bob_account, asset_gen,
                                           circulate_transfer_contract_gen, asset_name,
                                           supply, asset_type_name, precision,
                                           transfer_val):

    circ_tran_asset = asset_gen(asset_name, alice_account, supply, 
                                asset_type_name, precision)
    
    # Create the simulation with certain asset types
    sim_script = mk_circulate_transfer_script(asset_type_name, precision)
    simKey = rpc.uplink_sim_create(alice_account.address, sim_script)["simKey"]

    alice_addr = alice_account.address

    # Circulate half of supply to alice (asset issuer)
    result1 = rpc.uplink_sim_call(simKey, caller=alice_addr, method="circulate1", 
                                  args=[VAsset(circ_tran_asset.address), 
                                        transfer_val])
    assert is_rpc_ok(result1)

    # Transfer all holdings from alice to bob
    result2 = rpc.uplink_sim_call(simKey, caller=alice_addr, method="transfer1",
                                  args=[VAsset(circ_tran_asset.address),
                                        VAccount(alice_account.address),
                                        VAccount(bob_account.address),
                                        transfer_val])
    assert is_rpc_ok(result2)
            
    # Circulate remaining supply to alice (0 supply left)
    result3 = rpc.uplink_sim_call(simKey, caller=alice_addr, method='circulate2',
                                  args=[VAsset(circ_tran_asset.address),
                                        transfer_val])
    assert is_rpc_ok(result3)
    
    # entire asset supply should be circulated now
    assert(rpc.uplink_sim_query_asset(simKey, circ_tran_asset.address).supply == 0)

    # Transfer all from alice to bob (alice should have 0 holdings)
    result4 = rpc.uplink_sim_call(simKey, caller=alice_addr, method='transfer2',
                                  args=[VAsset(circ_tran_asset.address),
                                        VAccount(alice_account.address),
                                        VAccount(bob_account.address),
                                        transfer_val])
    assert is_rpc_ok(result4)

    asset = rpc.uplink_sim_query_asset(simKey, circ_tran_asset.address)
    # Bob should have all the holdings
    assert(asset.holdings[bob_account.address] == supply)
    assert (len(asset.holdings) == 1)


def mkFixed2(n):
    return VFixed(Decimal(str(n)), 2)

@pytest.mark.parametrize(("deposit", "initial_price", "final_price", "payout"), [
     (mkFixed2(1000.00), mkFixed2(7250.00), mkFixed2(6250.00), 100000),
     (mkFixed2(1000.00), mkFixed2(7250.00), mkFixed2(7250.00), 120000)
])
def test_principal_protected_simulation(rpc, alice_account, bob_account, asset_gen,
                                        deposit, initial_price, final_price, payout):

    days_between_final_and_maturity = 19 

    # account representing 3rd party data feed account on ledger
    data_feed_acc = per_test_account(rpc)

    # create principal protected asset on ledger
    pp_asset = asset_gen("protected", alice_account, 100000000, "Fractional", 2)

    # ----------  Aliases  ----------
    alice_addr = alice_account.address
    bob_addr = bob_account.address
    data_feed_addr = data_feed_acc.address
    def get_asset():
        return rpc.uplink_get_asset(pp_asset.address)
    # -------------------------------

    # circulate and transfer proper amount from issuer to investor
    t1 = rpc.uplink_circulate_asset(private_key=alice_account.private_key,
                                    from_address=alice_account.address,
                                    amount=100000000,
                                    asset_address=pp_asset.address)
    wait_until(lambda: get_asset().supply == 0)
    wait_until(lambda: get_asset().holdings[alice_account.address] == 100000000)
    t2 = rpc.uplink_transfer_asset(private_key=alice_account.private_key,
                                   from_address=alice_account.address,
                                   to_address=bob_account.address,
                                   balance=100000,
                                   asset_address=pp_asset.address)
    wait_until(lambda: get_asset().holdings[alice_account.address] == 99900000)
    wait_until(lambda: get_asset().holdings[bob_account.address] == 100000)

    # create simulation of principal protected contract
    pp_script = mk_principal_protected_script(alice_addr,
                                                data_feed_addr,
                                                pp_asset.address)
    simKey = rpc.uplink_sim_create(alice_account.address, pp_script)["simKey"]


    # Begin simulation logic
    # -----------------------

    # 0) set timestamp to before the closing date
    rpc.uplink_sim_update_set_time(simKey, "2018-02-02T00:00:00+00:00")
    # 1) initialize the contract with a deposit of 1000
    rpc.uplink_sim_call(simKey, caller=bob_addr, method="init", args=[deposit])
    # 2) set timestamp to after strike date but before final date
    rpc.uplink_sim_update_set_time(simKey, "2018-02-04T00:00:01+00:00")
    # 3) data feed account sets the close price
    rpc.uplink_sim_call(simKey, caller=data_feed_addr,
                        method="confirmation",
                        args=[initial_price])
    rpc.uplink_sim_update_add_timedelta(simKey, "1d")
    
    # 4) for every (business) day between the the final date and the maturity 
    #    date, the date feed account repeatedly calls into the contract to set
    #    close_price for that day, accumulating a running average.
    for i in range (0, days_between_final_and_maturity + 1):
        #    4i) data feed repeatedly sets the close  
        rpc.uplink_sim_call(simKey, caller=data_feed_addr,
                            method="calculate_level",
                            args=[final_price])
        rpc.uplink_sim_update_add_timedelta(simKey, "1d")

    # 5) the investor or issuer calls the last method, AFTER the finalDate, to
    #    to settle the contract in which the investor either gets back the
    #    deposit or the payout.
    rpc.uplink_sim_call(simKey, caller=alice_addr,
                        method="determine_final_level", 
                        args=[])

    # check if investor has $1950.00 holdings (deposit + (deposit * threshold_calc))
    underlying = rpc.uplink_sim_query_asset(simKey, pp_asset.address)
    assert (underlying.holdings[bob_addr] == payout)


@pytest.mark.parametrize(("account", "method_name", "var_name", "arg"), [
    ("alice_account", "fn_int", "a", VInt(404)),
    ("bob_account", "fn_float", "b", VFloat(2.123456789)),
    ("charlie_account", "fn_fixed5", "c", VFixed(Decimal("6.54321"),5)),
    ("charlie_account", "fn_fixed5", "c", VFixed(Decimal("-6.54321"), 5)),
    ("dave_account", "fn_fixed2", "c", VFixed(Decimal("6.54"), 2)),
    ("dave_account", "fn_fixed2", "c", VFixed(Decimal("2.00"), 2)),
    ("alice_account", "fn_bool", "d", VBool(False)),
    ("alice_account", "fn_msg", "e", VMsg("Hello World")),
    ("alice_account", "fn_account", "f", VAccount(testAddr)),
    ("bob_account", "fn_assetDisc", "g", VAsset(testAddr)),
    ("bob_account", "fn_assetBin", "g0", VAsset(testAddr)),
    ("charlie_account", "fn_assetFrac1", "g1", VAsset(testAddr)),
    ("alice_account", "fn_assetFrac2", "g2", VAsset(testAddr)),
    ("alice_account", "fn_assetFrac3", "g3", VAsset(testAddr)),
    ("alice_account", "fn_assetFrac4", "g4", VAsset(testAddr)),
    ("bob_account", "fn_assetFrac5", "g5", VAsset(testAddr)),
    ("alice_account", "fn_assetFrac6", "g6", VAsset(testAddr)),
    ("alice_account", "fn_contract", "h", VContract(testAddr)),
    ("alice_account", "fn_datetime", "i", VDateTime(datetime.datetime.now())),
    ("alice_account", "fn_enum", "k", VEnum("Foo"))
])
def test_all_args_contract(rpc, all_args_contract, alice_account, bob_account,
        charlie_account, dave_account, account, method_name, var_name, arg):
   
    accounts = { "alice_account" : alice_account
               , "bob_account" : bob_account
               , "charlie_account" : charlie_account
               , "dave_account" : dave_account
               }
   
    address = accounts[account].address
    priv_key = accounts[account].private_key

    txhash = rpc.uplink_call_contract(private_key=priv_key, from_address=address,
                                      contract_addr=all_args_contract.address,
                                      method=method_name,
                                      args=[arg])
    wait_until_tx_accepted(rpc, txhash)

    def get_contract_storage():
        storage = rpc.uplink_get_contract(all_args_contract.address).storage
        return storage

    # Intially, all top level values in the all_args_contract are undefined. We
    # set them by making a function call, and resultingly they should not be
    # undefined.
    assert get_contract_storage()[var_name]["contents"] is not None

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


def test_get_contract_callable(rpc, all_args_contract, alice_account,
        bob_account, charlie_account, dave_account):
    
    alice_addr = alice_account.address
    bob_addr = bob_account.address
    charlie_addr = charlie_account.address
    dave_addr = dave_account.address
    
    result = rpc.uplink_get_contract_callable(all_args_contract.address)
    assert result == {u'fn_int': [[alice_addr],[[u'a_', u'int']]],
                      u'fn_float': [[bob_addr],[[u'b_', u'float']]],
                      u'fn_fixed5': [[charlie_addr],[[u'c_', u'fixed5']]],
                      u'fn_fixed2': [[dave_addr],[[u'l_', u'fixed2']]],
                      u'fn_bool': [sorted([alice_addr,bob_addr]),[[u'd_', u'bool']]],
                      u'fn_msg': [sorted([alice_addr,charlie_addr]),[[u'e_', u'msg']]],
                      u'fn_account': [sorted([alice_addr,dave_addr]),[[u'f_', u'account']]],
                      u'fn_assetDisc': [sorted([bob_addr,charlie_addr]),[[u'g_',
                          u'assetDisc']]],
                      u'fn_assetBin':
                          [sorted([bob_addr,dave_addr]),[[u'g0_', u'assetBin']]],
                      u'fn_assetFrac1':
                          [sorted([charlie_addr,dave_addr]),[[u'g1_', u'assetFrac1']]],
                      u'fn_assetFrac2':
                          [sorted([alice_addr,bob_addr,charlie_addr]),[[u'g2_', u'assetFrac2']]],
                      u'fn_assetFrac3':
                          [sorted([alice_addr,bob_addr,dave_addr]),[[u'g3_', u'assetFrac3']]],
                      u'fn_assetFrac4':
                          [sorted([alice_addr,charlie_addr,dave_addr]),[[u'g4_',u'assetFrac4']]],
                      u'fn_assetFrac5':
                          [sorted([bob_addr,charlie_addr,dave_addr]),[[u'g5_', u'assetFrac5']]],
                      u'fn_assetFrac6': 
                          [sorted([alice_addr,bob_addr,charlie_addr,dave_addr]),[[u'g6_', u'assetFrac6']]],
                      u'fn_contract': [[],[[u'h_', u'contract']]],
                      u'fn_datetime': [[],[[u'i_', u'datetime']]],
                      u'fn_enum': [[],[[u'k_', u'enum testEnum']]],
                      u'never_called': [[],[]]
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
    assert (version_info["version"] == __version__)


def test_query(rpc, alice_account):
    q1 = "QUERY contracts WHERE state = 'initial';"
    q2 = "QUERY assets WHERE assetType = 'Discrete';"
    q3 = "QUERY accounts WHERE address = '{}';".format(alice_account.address)
    q4 = "QUERY transactions WHERE tx_type = 'CreateAccount';"

    a1 = rpc.uplink_query(q1)
    a2 = rpc.uplink_query(q2)
    a3 = rpc.uplink_query(q3)
    a4 = rpc.uplink_query(q4)

    assert len(a1) >= 0
    assert len(a2) >= 0
    assert len(a3) >= 0
    assert len(a4) >= 0


def test_get_invalid_tx_missing_fail(rpc):
    result = rpc.uplink_get_invalid_transaction("nothing")
    assert result.get('errorMsg')


def test_get_invalid_tx_missing(rpc, alice_account, bob_account, gold_asset):
    tx_hash = rpc.uplink_transfer_asset(
        private_key=bob_account.private_key,
        from_address=bob_account.address,
        to_address=alice_account.address,
        balance=50000000,
        asset_address=gold_asset.address,
    )

    wait_until_tx_processed(rpc, tx_hash)

    result = rpc.uplink_get_invalid_transaction(tx_hash)
    assert result.get("reason")

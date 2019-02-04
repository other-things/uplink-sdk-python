import time

import os
import pytest

from uplink.exceptions import TransactionRejected
from uplink.client import UplinkJsonRpcError, UplinkJsonRpc, Account
from uplink.cryptography import ecdsa_new

testAddr = 'fwBVDsVh8SYQy98CzYpNPcbyTRczVUZ96HszhNRB8Ve'
host = os.getenv('RPC_HOST', 'localhost')


@pytest.fixture(scope='session')
def rpc():
    return UplinkJsonRpc(host=host)


@pytest.fixture
def per_test_account(rpc):
    pk, sk = ecdsa_new()
    tx_hash, address = rpc.uplink_create_account(
        private_key=sk,
        public_key=pk,
        from_address=None,
        metadata={},
        timezone="GMT"
    )
    wait_until_tx_accepted(rpc, tx_hash)
    account = rpc.uplink_get_account(address)
    assert isinstance(account, Account)
    # Attach the new account's private key so that these account objects can
    # sign off on transactions issued in the integration tests.
    setattr(account, 'private_key', sk)
    return account


@pytest.fixture(scope='session')
def alice_account(rpc):
    return per_test_account(rpc)


@pytest.fixture(scope='session')
def bob_account(rpc):
    return per_test_account(rpc)

@pytest.fixture(scope='session')
def charlie_account(rpc):
    return per_test_account(rpc)

@pytest.fixture(scope='session')
def dave_account(rpc):
    return per_test_account(rpc)

@pytest.fixture(scope="session")
def asset_gen(rpc):
    def _asset(asset_name, issuer_account, supply, asset_type_nm, precision=None, metadata=None):
        if metadata is None:
            metadata = {}
        tx_hash, address = rpc.uplink_create_asset(
            private_key=issuer_account.private_key,
            origin=issuer_account.address,
            name=asset_name,
            supply=supply,
            asset_type_nm=asset_type_nm,
            reference="Token",
            issuer=issuer_account.address,
            precision=precision,
            metadata=metadata
        )
        wait_until_tx_accepted(rpc, tx_hash)
        asset = rpc.uplink_get_asset(address)
        return asset

    return _asset


@pytest.fixture(scope="session")
def gold_asset(rpc, asset_gen, alice_account):
    asset = asset_gen("Gold", alice_account, 10000, "Discrete")
    return asset


@pytest.fixture(scope="session")
def silver_asset(rpc, asset_gen, bob_account):
    asset = asset_gen("Silver", bob_account, 10000, "Discrete", metadata={"colour": "red"})
    return asset


@pytest.fixture(scope="session")
def platinum_asset(rpc, asset_gen, bob_account):
    asset = asset_gen("Platinum", bob_account, 10000, asset_type_nm="Fractional", precision=2)
    return asset


@pytest.fixture(scope="session")
def contract_gen(rpc, alice_account):
    def _contract(script):
        tx_hash, address = rpc.uplink_create_contract(
            private_key=alice_account.private_key,
            from_address=alice_account.address,
            script=script)

        wait_until_tx_accepted(rpc, tx_hash)
        contract = rpc.uplink_get_contract(address)
        return contract

    return _contract


@pytest.fixture(scope="session")
def example_contract(contract_gen):
    contract = contract_gen(script="""
global int x = 0 ;

transition initial -> set;
transition set -> terminal;

@set
end () {
  terminate("Now I die.");
}

@initial
setX (int y) {
  x = 42;
  transitionTo(:set);
}"""
                            )

    return contract


@pytest.fixture(scope="session")
def oracle_contract(contract_gen):
    contract = contract_gen(script="""
    global datetime timestamp;
global float value;

transition initial -> end;
transition end -> end;
transition end -> terminal;

@initial
set(float v) {
  if (sender() == deployer()) {
    timestamp = now();
    value = v;
  };
  transitionTo(:end);
}

@end
end() {
  if (sender() == deployer()) {
    terminate("This is the end");
  } else {
    stay();
  };
}"""
                            )

    return contract


@pytest.fixture(scope="session")
def all_args_contract(contract_gen, alice_account, bob_account, charlie_account, dave_account):

    contract = contract_gen(script="""

enum testEnum {{ Foo, Bar }};

int a;
float b;
fixed5 c;
bool d;
msg e;
account f;
assetDisc g;
assetBin  g0;
assetFrac1 g1;
assetFrac2 g2;
assetFrac3 g3;
assetFrac4 g4;
assetFrac5 g5;
assetFrac6 g6;
contract h;
datetime i;
void j;
enum testEnum k;
fixed2 l;

global account alice = u'{0}';
global account bob = u'{1}';
global account charlie = u'{2}';
global account dave = u'{3}';

transition initial -> initial;
transition initial -> end;
transition end -> end;
transition end -> terminal;

@initial [ roles : {{ alice }} ]
fn_int(int a_) {{
    a = a_;
    stay();
}}

@initial [ roles : {{ bob }} ]
fn_float(float b_) {{
    b = b_;
    stay();
}}

@initial [ roles : {{ charlie }} ]
fn_fixed5(fixed5 c_) {{
    c = c_;
    stay();
}}

@initial [ roles : {{ dave }} ]
fn_fixed2(fixed2 l_) {{
    l = l_;
    stay();
}}


@initial [ roles : {{ alice, bob }} ]
fn_bool(bool d_) {{
    d = d_;
    stay();
}}

@initial [ roles : {{ alice , charlie }} ]
fn_msg(msg e_) {{
    e = e_;
    stay();
}}

@initial [ roles : {{ alice, dave }} ]
fn_account(account f_) {{
    f = f_;
    stay();
}}

@initial [ roles : {{ bob, charlie }} ]
fn_assetDisc(assetDisc g_) {{
    g = g_;
    stay();
}}

@initial [ roles : {{ bob, dave }} ]
fn_assetBin(assetBin g0_) {{
    g0 = g0_;
    stay();
}}

@initial [ roles : {{ charlie, dave }} ]
fn_assetFrac1(assetFrac1 g1_) {{
    g1 = g1_;
    stay();
}}

@initial [ roles : {{ alice, bob, charlie }} ]
fn_assetFrac2(assetFrac2 g2_) {{
    g2 = g2_;
    stay();
}}

@initial [ roles : {{ alice, bob, dave }} ]
fn_assetFrac3(assetFrac3 g3_) {{
    g3 = g3_;
    stay();
}}

@initial [ roles : {{ alice, charlie, dave }} ]
fn_assetFrac4(assetFrac4 g4_) {{
    g4 = g4_;
    stay();
}}

@initial [ roles : {{ bob, charlie, dave }} ]
fn_assetFrac5(assetFrac5 g5_) {{
    g5 = g5_;
    stay();
}}

@initial [ roles : {{ alice, bob, charlie, dave }} ]
fn_assetFrac6(assetFrac6 g6_) {{
    g6 = g6_;
    stay();
}}

@initial
fn_contract(contract h_) {{
    h = h_;
    stay();
}}


@initial
fn_datetime(datetime i_) {{
    i = i_;
    stay();
}}

@initial
fn_enum(enum testEnum k_) {{
    k = k_;
    stay();
}}

@initial
never_called() {{
    transitionTo(:end);
}}

@end
end() {{
  if (sender() == deployer()) {{
    terminate("This is the end");
  }} else {{
    stay();
  }};
}}
""".format(alice_account.address, bob_account.address, charlie_account.address, dave_account.address))

    return contract


@pytest.fixture(scope="session")
def contract_using_oracle_contract(contract_gen):
    contract = contract_gen(script="""
global float x = 0.0;

transition initial -> set;
transition set -> terminal;

@initial
setX (float y, contract oracle) {
  x = y * contractValue(oracle, "value");
  transitionTo(:set);
}

@set
end () {
  terminate("Now I die.");
}""")
    return contract


@pytest.fixture(scope="session")
def circulate_transfer_contract_gen(contract_gen):
    def _circulate_transfer_contract_gen(asset_type_name, precision):
        _script = mk_circulate_transfer_script(asset_type_name, precision)
        contract = contract_gen(script=_script)
        return contract

    return _circulate_transfer_contract_gen


def mk_circulate_transfer_script(asset_type_name, precision):
    _asset_type_name = "asset"
    holdings_type_name = ""
    if asset_type_name == "Discrete":
        _asset_type_name += "Disc"
        holdings_type_name = "int"
    elif asset_type_name == "Binary":
        _asset_type_name += "Bin"
        holdings_type_name = "bool"
    elif asset_type_name == "Fractional" and precision is not None:
        _asset_type_name += "Frac" + str(precision)
        holdings_type_name = "fixed" + str(precision)
    else:
        raise ValueError("Argument must be 'Discrete', 'Binary', or 'Fractional'")

    script = """
transition initial -> circulated1;
transition circulated1 -> transferred1;
transition transferred1 -> circulated2;
transition circulated2 -> terminal;

@initial
circulate1({0} a, {1} amount) {{
  circulate(a,amount);
  transitionTo(:circulated1);
}}

@circulated1
transfer1({0} a, account from, account to, {1} amount) {{
  transferHoldings(from,a,amount,to);
  transitionTo(:transferred1);
}}

@transferred1
circulate2({0} a, {1} amount) {{
  circulate(a,amount);
  transitionTo(:circulated2);
}}

@circulated2
transfer2({0} a, account from, account to, {1} amount) {{
  transferHoldings(from,a,amount,to);
  transitionTo(:terminal);
}}
""".format(_asset_type_name, holdings_type_name)
    return script


def mk_principal_protected_script(issuer, datafeed, asset):
    script = """
global account issuer = u'{0}';
global account datafeed = u'{1}';
global account investor;

global assetFrac2 asset_ = a'{2}';
global fixed2 minimum_deposit = 1000.00f;
global fixed2 return_calc = 0.20f;
global fixed2 threshold_calc = 0.95f;
global fixed2 deposit = 0.00f;

global datetime closingDate  = "2018-02-03T00:00:00+00:00";
global datetime strikeDate   = "2018-02-04T00:00:00+00:00";
global datetime finalDate    = "2018-02-05T00:00:00+00:00";
global datetime maturityDate = "2018-02-24T00:00:00+00:00";

global fixed2 counter = 0.00f;
global fixed2 closing_level_sum = 0.00f;
global fixed2 initial_price;
global fixed2 final_price;
global fixed2 payout;

transition initial -> confirmation;
transition initial -> terminal;
transition confirmation -> calculate_level;
transition calculate_level -> determine_final_level;
transition determine_final_level -> terminal;
transition initial -> initial;
transition confirmation -> confirmation;
transition calculate_level -> calculate_level;
transition determine_final_level -> determine_final_level;

@initial
init(fixed2 new_deposit) {{
   if (now() < closingDate) {{
      if((sender() != issuer) && (new_deposit >= minimum_deposit)) {{
         investor = sender();
         deposit = new_deposit;
         transferHoldings(investor, asset_, deposit, issuer);
         transitionTo(:confirmation);
      }} else {{
         stay();
      }};
   }} else {{
      transitionTo(:terminal);
   }};
}}

@confirmation
confirmation(fixed2 close_price) {{
   if ((now() > strikeDate) && (sender() == datafeed)) {{
    initial_price = close_price;
    transitionTo(:calculate_level);
   }} else {{
    stay();
   }};
}}

@calculate_level
calculate_level(fixed2 close_price) {{
   if ((now() > finalDate) && (now() < maturityDate) && (sender() == datafeed) && isBusinessDayUK(now())) {{
     closing_level_sum = closing_level_sum + close_price;
     counter = counter + 1.00f;
   }};

   if (now() > maturityDate) {{
     transitionTo(:determine_final_level);
   }} else {{
     stay();
   }};
}}

@determine_final_level
determine_final_level() {{
   if ((now() > maturityDate) && (sender() == investor) || (sender() == issuer)) {{
     final_price = closing_level_sum / counter;
     if((final_price > (initial_price * threshold_calc))) {{
       payout = (deposit + (deposit * return_calc));
       transferHoldings(issuer, asset_, payout, investor);
       terminate("returning deposit and profit");
     }} else {{
       transferHoldings(issuer, asset_, deposit, investor);
       terminate("returning deposit");
     }};
   }} else {{
     stay();
   }};
}}
""".format(issuer, datafeed, asset)
    return script


def wait_until_tx_accepted(rpc, tx_hash):
    status = wait_until_tx_processed(rpc, tx_hash)
    if status == "Accepted":
        return
    else:
        raise TransactionRejected(tx_hash, status)


def wait_until_tx_processed(rpc, tx_hash):
    """
    Wait until a transaction has been either Accepted or Rejected
    """
    query_tx_status = rpc.uplink_get_transaction_status
    wait_until(lambda: query_tx_status(tx_hash) in ["NonExistent", "Accepted", "Rejected"])
    return query_tx_status(tx_hash) 

def wait_until(pred, tries=20, delay=1):
    """
    Wait until predicate is true, else fail

    :param pred:
    :param tries:
    :param delay:
    """
    while tries != 0:
        time.sleep(delay)
        tries -= 1
        if pred():
            return

    raise TimeoutError("Timed out in wait_until")

def wait_until_doesnt_raise(f, exception, **kwargs):
    """

    :param f:
    :param exception:
    :param kwargs:
    :return: result of f()
    """

    def pred():
        try:
            f()
        except exception:
            return False
        else:
            return True

    wait_until(pred, **kwargs)
    return f()


def is_rpc_ok(result):
    return result.get("tag") in ["RPCRespOK","RPCTransactionOK"]

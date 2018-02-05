import time

import os
import pytest

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
    account = rpc.uplink_create_account(
        private_key=sk,
        public_key=pk,
        from_address=None,
        metadata={},
        timezone="GMT"
    )
    account = wait_until_doesnt_raise(
        lambda: rpc.uplink_get_account(account.address), UplinkJsonRpcError)

    assert isinstance(account, Account)
    setattr(account, 'public_key', pk)
    setattr(account, 'private_key', sk)
    return account


@pytest.fixture(scope='session')
def alice_account(rpc):
    return per_test_account(rpc)


@pytest.fixture(scope='session')
def bob_account(rpc):
    return per_test_account(rpc)


@pytest.fixture(scope="session")
def asset_gen(rpc):
    def _asset(asset_name, issuer_account, supply=10000, asset_type_nm="Discrete", precision=None):
        status, address = rpc.uplink_create_asset(
            private_key=issuer_account.private_key,
            origin=issuer_account.address,
            name=asset_name,
            supply=supply,
            asset_type_nm=asset_type_nm,
            reference="Token",
            issuer=issuer_account.address,
            precision=precision
        )
        assert is_rpc_ok(status)
        asset = wait_until_doesnt_raise(
            lambda: rpc.uplink_get_asset(address), UplinkJsonRpcError)
        return asset

    return _asset


@pytest.fixture(scope="session")
def gold_asset(rpc, asset_gen, alice_account):
    asset = asset_gen("Gold", alice_account)
    return asset


@pytest.fixture(scope="session")
def silver_asset(rpc, asset_gen, bob_account):
    asset = asset_gen("Silver", bob_account)
    return asset

@pytest.fixture(scope="session")
def platinum_asset(rpc, asset_gen, bob_account):
    asset = asset_gen("Platinum", bob_account, asset_type_nm="Fractional", precision=2)
    return asset


@pytest.fixture(scope="session")
def contract_gen(rpc, alice_account):
    def _contract(script):
        status, address = rpc.uplink_create_contract(
            private_key=alice_account.private_key,
            from_address=alice_account.address,
            script=script)
        assert is_rpc_ok(status)

        return wait_until_doesnt_raise(
            lambda: rpc.uplink_get_contract(address), UplinkJsonRpcError)

    return _contract


@pytest.fixture(scope="session")
def example_contract(contract_gen):
    contract = contract_gen(script="""
global int x = 0 ;

transition initial -> get;
transition get -> terminal;

@get
getX () {
  terminate("Now I die.");
  return x;
}

@initial
setX (int y) {
  x = 42;
  transitionTo(:get);
  return void;
}"""
                            )

    return contract


@pytest.fixture(scope="session")
def oracle_contract(contract_gen):
    contract = contract_gen(script="""
    global datetime timestamp;
global float value;

transition initial -> end;
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
  };
}"""
                            )

    return contract


@pytest.fixture(scope="session")
def all_args_contract(contract_gen):

    contract = contract_gen(script="""

int a;
float b;
fixed5 c;
bool d;
msg e;
account f;
asset g;
contract h;
datetime i;
void j;

transition initial -> end;
transition end -> terminal;

@initial
fn_int(int a_) {
    a = a_;
}

@initial
fn_float(float b_) {
    b = b_;
}

@initial
fn_fixed5(fixed5 c_) {
    c = c_;
}

@initial
fn_bool(bool d_) {
    d = d_;
}

@initial
fn_msg(msg e_) {
    e = e_;
}

@initial
fn_account(account f_) {
    f = f_;
}

@initial
fn_asset(asset g_) {
    g = g_;
}

@initial
fn_contract(contract h_) {
    h = h_;
}


@initial
fn_datetime(datetime i_) {
    i = i_;
}

@initial
never_called() {
    transitionTo(:end);
}

@end
end() {
  if (sender() == deployer()) {
    terminate("This is the end");
  };
}
""")

    return contract


@pytest.fixture(scope="session")
def contract_using_oracle_contract(contract_gen):
    contract = contract_gen(script="""
global float x = 0.0;

transition initial -> get;
transition get -> terminal;

@initial
setX (float y, contract oracle) {
  x = y * contractValue(oracle, "value");
  transitionTo(:get);
}

@get
getX () {
  terminate("Now I die.");
  return x;
}""")
    return contract


@pytest.fixture(scope="session")
def alice_circulate_transfer_asset(rpc, asset_gen, alice_account):
    asset = asset_gen("CircTran", alice_account, 10000)
    return asset


@pytest.fixture(scope="session")
def contract_circulate_transfer(contract_gen):
    contract = contract_gen(script="""
transition initial -> circulated1;
transition circulated1 -> transferred1;
transition transferred1 -> circulated2;
transition circulated2 -> terminal;

@initial
circulate1(asset a, int amount) {
  circulate(a,amount);
  transitionTo(:circulated1);
}

@circulated1
transfer1(asset a, account from, account to, int amount) {
  transferHoldings(from,a,amount,to);
  transitionTo(:transferred1);
}

@transferred1
circulate2(asset a, int amount) {
  circulate(a,amount);
  transitionTo(:circulated2);
}

@circulated2
transfer2(asset a, account from, account to, int amount) {
  transferHoldings(from,a,amount,to);
  transitionTo(:terminal);
}
""")

    return contract


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

    pytest.fail("Timed out")


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
    return result.get("tag") == "RPCRespOK"

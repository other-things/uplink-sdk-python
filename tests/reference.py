from ecdsa.keys import *
from ecdsa.ecdsa import Public_key, generator_secp256k1, curve_secp256k1
from ecdsa.curves import *

from uplink import *

# uplink testPriv
d = 72637887363324669071595225655990695893413546682343152974463667925881860469868

# uplink testPub
Qx = 79174541683660805620639640382768661759397823295690888507762753093299621916987
Qy = 71065057682299419085325030940046895916159750330092956837115984315857371796477

# uplink testAddr
testAddr = 'fwBVDsVh8SYQy98CzYpNPcbyTRczVUZ96HszhNRB8Ve'

# Public Key
point = ellipticcurve.Point(curve_secp256k1, Qx, Qy)
pubk = Public_key(generator_secp256k1, point)
vkey = VerifyingKey.from_public_point(point, curve=SECP256k1)
skey = SigningKey.from_secret_exponent(d, curve=SECP256k1)

# Assets
assetAddr = '43WRxMNcnYgZFcE36iohqrXKQdajUdAxeSn9mzE1ZedB'
toAddr = '7mR5d7s6cKB4qjuX1kiwwNtygfURhFQ9TKvEd9kmq6QL'

testSig = \
  (115136800820456833737994126771386015026287095034625623644186278108926690779567,
  98245280522003505644797670843107276132602050133082625768706491602875725788467)

testTimestamp = 1231006505

nonce = 42

test_args = [
    VInt(1), VFloat(3.5), VBool(True),VFixed(Decimal("3.223"), 3),
    VAddress(testAddr), VAccount(testAddr),
    VAsset(testAddr), VContract(testAddr),
    VMsg("Hello world"),
    VVoid,
    VUndefined
]

#------------------------------------------------------------------------
# Transactions
#------------------------------------------------------------------------


def _testTransfer():
    to_addr = toAddr
    asset_addr = assetAddr
    balance = 5
    return TransferAssetHeader(asset_addr, to_addr, balance)


def _testCreateAccount():
    public_key_hex = hexkey(vkey)
    metadata = dict(stuff="key", bax="foo", fax="bar")
    address = derive_account_address(vkey)
    timezone = "GMT"

    return CreateAccountHeader(public_key_hex, metadata, address, timezone)


def _testCreateAsset():
    name = "test"
    supply = 1000
    asset_type = "Discrete"
    ref = "Token"
    issuer = testAddr
    precision = None
    timestamp = testTimestamp 

    return CreateAssetHeader(name, supply, asset_type,
                             ref, issuer, precision, timestamp)


def _testCreateContract():
    script = ""
    address = assetAddr
    timestamp = testTimestamp
    return CreateContractHeader(script, testAddr, address, timestamp)


def _testRevokeAccount():
    account_addr = testAddr
    return RevokeAccountHeader(account_addr)


def testCall(args):
    contract_addr = testAddr
    method = "get"
    return CallHeader(contract_addr, method, args)


def _testBind():
    assetAddr_ = assetAddr
    contractAddr = toAddr
    (r,s) = testSig
    proof = pack_signature(r,s)
    return BindHeader(assetAddr_, contractAddr, proof)


def testTx(tx_type, wrapper, hdr):
    time = testTimestamp
    r, s = hdr.sign(skey, k=nonce)
    sig = pack_signature(r, s)
    origin = testAddr

    tx_hdr = tx_type(wrapper(hdr))
    return Transaction(tx_hdr, sig, time, origin=origin)

testTransfer = _testTransfer()
testCreateAccount = _testCreateAccount()
testCreateAsset = _testCreateAsset()
testCreateContract = _testCreateContract()
testRevokeAccount = _testRevokeAccount()
testBind = _testBind()

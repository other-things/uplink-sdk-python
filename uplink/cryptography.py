import time
import sha3
import base64
import hashlib
import struct
import codecs
from base58 import b58encode, b58decode
from ecdsa import SigningKey, SECP256k1, util, ellipticcurve, VerifyingKey

#------------------------------------------------------------------------
# Time
#------------------------------------------------------------------------


def get_time():
    """Get Time In Microseconds"""
    timestamp = int(time.time() * 1000000)
    return timestamp

#------------------------------------------------------------------------
# Hashing
#------------------------------------------------------------------------


def sha256(data):
    """Hash sha256 once"""
    return hashlib.sha256(data).hexdigest()


def sha256d(data):
    """Hash sha256 twice"""
    return hashlib.sha256(hashlib.sha256(data))

#------------------------------------------------------------------------
# Address Derivation
#------------------------------------------------------------------------


def derive_contract_address(ts, script):
    """Contract address derives from storage"""

    hashed = hashlib.sha3_256((str(ts) + script).encode()).digest()
    contract_address = b58encode(hashed)
    return contract_address


def derive_asset_address(name, issuer, supply, mref, typ, timestamp):
    
    n = name.encode()
    i = b58decode(issuer)
    s = struct.pack(">Q", supply)

    mrefPref = 0 if (mref is None) else 1
    mrefPrefBS = struct.pack(">B", mrefPref)
    mrefLenBS = b'' if (mref is None) else struct.pack(">H", len(mref))
    mrefBS = b'' if (mref is None) else mref.encode()
    refBS = mrefPrefBS + mrefLenBS + mrefBS 

    tBS = typ.to_binary()
    ts = struct.pack(">Q", timestamp)
    
    final = n + i + s + refBS + tBS + ts
    finalHash = hashlib.sha3_256(final).digest()

    addr = b58encode(finalHash)
    return addr


def derive_account_address(pubkey):
    """Account address derives from public key: b58(sha256(sha256(ripemd160(sha256(pubkey)))))"""
    x = pubkey.pubkey.point.x()
    y = pubkey.pubkey.point.y()

    sha_step1 = hashlib.sha3_256((str(x) + str(y)).encode()).digest()

    ripe = hashlib.new('ripemd160')
    ripe.update(sha_step1)
    ripe = ripe.digest()

    sha_step2 = hashlib.sha3_256(ripe).digest()
    sha_step3 = hashlib.sha3_256(sha_step2)

    address = b58encode(sha_step3.digest())
    return address


#------------------------------------------------------------------------
# Digital Signatures
#------------------------------------------------------------------------


# SEPP2561 Curve instead of default NIST
order = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def ecdsa_new():
    """Create a new ecdsa key pair returns (publickey, privatekey)"""
    sk = SigningKey.generate(curve=SECP256k1, hashfunc=sha3.sha3_256)
    pk = sk.verifying_key
    return (pk, sk)


def ecdsa_pub(x, y):
    """Create a public key from a public point"""
    point = ellipticcurve.Point(SECP256k1, x, y)
    return VerifyingKey.from_public_point(point, curve=SECP256k1)


def pub_to_xy(public_key):
    """Public Key encoding"""
    x = public_key.pubkey.point.x()
    y = public_key.pubkey.point.y()
    concat = str(x) + ":" + str(y)
    key = b58encode(codecs.encode(concat, 'hex'))
    return key


def read_key(filename):
    """open saved key"""
    with open(filename, "rb") as file:
        pemkey = file.read()
        private_key = SigningKey.from_pem(pemkey)
        return private_key


def save_key(sk, name):
    """save key as pem format"""
    filename = "{}.pem".format(name)
    with open(filename, "wb") as file:
        file.write(sk)
    return 'name'


def ecdsa_sign(sk, msg, k=None):
    """Sign ecdsa"""
    sig = sk.sign(msg, hashfunc=sha3.sha3_256, k=k)
    signature = util.sigdecode_string(sig, order)

    return signature  # matches haskell output


def pack_signature(r, s):
    """Combine R&S

    Note: This serialization exactly reflects de/serialization written in the
    uplink backend. Modifying the way ECDSA signatures are serialized may cause
    transactions sent by this SDK to be deemed invalid by the uplink node.

    """
    rb = str(r)
    lenrb = struct.pack(">h", len(rb))
    rEnc = lenrb + rb.encode()

    sb = str(s)
    lensb = struct.pack(">h", len(sb))
    sEnc = lensb + sb.encode()
    signature = base64.b64encode('{}:{}'.format(rEnc.decode(), sEnc.decode()).encode())
    return signature


def ecdsa_verify(pk, sig, msg):
    """Verify ecdsa"""
    r, s = sig
    sigg = util.sigencode_string(r, s, order)
    return pk.verify(sigg, msg)


def make_qrcode(data, name):
    """Make QR codes"""
    import qrcode
    import base64
    from qrcode.image.pure import PymagingImage

    img = qrcode.make(data, image_factory=PymagingImage)
    filename = "{}.png".format(name)
    img.save(open(filename, "w+"))

    with open(filename, "rb") as image:
        encoded_img = base64.b64encode(image.read())
    return encoded_img

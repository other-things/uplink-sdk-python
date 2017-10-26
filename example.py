from uplink import *

rpc = UplinkJsonRpc()


def create_account(pk=None, sk=None):
    """Create Account Example"""
    if(pk is None):
        pk, sk = ecdsa_new()
    metadata = {}

    acct = rpc.uplink_create_account(
        private_key=sk,
        public_key=pk,
        from_address=None,
        metadata=metadata,
        timezone="GMT"
    )
    print(acct)
    return acct


def create_asset(sk, acct_address, asset_name, supply):
    """Create Asset Example"""
    asset = rpc.uplink_create_asset(
        private_key=sk,
        origin=acct_address,
        name=asset_name,
        supply=supply,
        asset_type="Discrete",
        reference="Token",
        issuer=acct_address,
        precision=0
    )

    print(asset)
    return asset


def transfer_assets(from_skey, from_addr, to_addr, balance, asset_addr):
    """Transfer Asset Example"""
    results = rpc.uplink_transfer_asset(private_key=from_skey, from_address=from_addr, to_address=to_addr,
                                        balance=balance, asset_address=asset_addr)
    return results


def create_contract(sk, acct_address, script):
    """CREATE CONTRACT EXAMPLE"""

    result = rpc.uplink_create_contract(sk, acct_address, script)
    print(result)
    return result


if __name__ == '__main__':
    # Create Public (pk) and Private (sk) ECDSA key pair
    pk, sk = ecdsa_new()

    # Use actual address after creating
    acct_addr = 'fwBVDsVh8SYQy98CzYpNPcbyTRczVUZ96HszhNRB8Ve'
    asset_addr = 'fwBVDsVh8SYQy98CzYpNPcbyTRczVUZ96HszhNRB8Ve'
    to_address = 'fwBVDsVh8SYQy98CzYpNPcbyTRczVUZ96HszhNRB8Ve'

    transfer_amount = 30  # TRANSFER SUPPLY
    supply = 100000  # ASSET SUPPLY
    asset_name = "USD"
    script = "INSERT SCRIPT HERE"

    create_account(pk, sk)
    create_asset(sk, acct_addr, asset_name, supply)
    create_contract(sk, acct_addr, script)
    transfer_assets(sk, acct_addr, to_address, transfer_amount, asset_addr)

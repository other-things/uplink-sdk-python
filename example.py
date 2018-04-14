from uplink import *

rpc = UplinkJsonRpc()


def create_account(pk=None, sk=None, metadata={}):
    """Create Account Example"""
    if(pk is None):
        pk, sk = ecdsa_new()

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
        asset_type_nm="Discrete",
        reference="Token",
        issuer=acct_address,
    )

    print(asset)
    return asset


def transfer_assets(from_skey, from_addr, to_addr, balance, asset_addr):
    """Transfer Asset Example"""
    results = rpc.uplink_transfer_asset(private_key=from_skey, from_address=from_addr, to_address=to_addr,
                                        balance=balance, asset_address=asset_addr)
    print(results)
    return results


def create_contract(sk, acct_address, script):
    """CREATE CONTRACT EXAMPLE"""

    result = rpc.uplink_create_contract(sk, acct_address, script)
    print(result)
    return result


def circulate_asset(sk, from_addr, amount, asset_addr):
    """Circulate Asset Example"""

    result = rpc.uplink_circulate_asset(sk, from_addr, amount, asset_addr)
    print(result)
    return result


if __name__ == '__main__':
    # Create Public (pk) and Private (sk) ECDSA key pair
    pk1, sk1 = ecdsa_new()
    pk2, sk2 = ecdsa_new()

    transfer_amount = 1000  # TRANSFER SUPPLY
    supply = 100000  # ASSET SUPPLY
    asset_name = "USD"
    script = "INSERT SCRIPT HERE"

    # Create a first account for 'Alice'
    new_account_1 = create_account(pk1, sk1, {'Name': 'Alice'})
    # Create a second account for 'Bob'
    new_account_2 = create_account(pk2, sk2, {'Name': 'Bob'})
    # Create a new asset with Alice's account
    new_asset = create_asset(sk1, new_account_1.address, asset_name, supply)
    # Create a new contract with Alice's account
    create_contract(sk1, new_account_1.address, script)
    # Circulate 75% of the asset to Alice's account
    circulate_asset(sk1, new_account_1.address, (supply * 0.75), new_asset[1])
    # Transfer the 'transfer_amount' from Alice to Bob
    transfer_assets(sk1, new_account_1.address, new_account_2.address, transfer_amount, new_asset[1])

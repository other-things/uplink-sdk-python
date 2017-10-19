<p align="center">
  <a href="http://www.adjoint.io"><img src="https://www.adjoint.io/images/logo-small.png" width="250"/></a>
</p>
<h3 align="center">Community Edition</h3>

Python SDK
==========

[![CircleCI](https://circleci.com/gh/adjoint-io/uplink-sdk-python.svg?style=svg)](https://circleci.com/gh/adjoint-io/uplink-sdk-python)

Installation
------------

```bash
$ pip install uplink-sdk-py
```

Testing
-------

```bash
$ pytest -vv test
$ pytest -vv integration_tests
```

Usage
-----

For example usage see [example.py](example.py).

Most of the following examples will show and explain the simple usage of the
``uplink-sdk-py``. Usage of the SDK can be divided into two types of actions,
querying the Uplink Ledger for data or acting on it - called *transactions*.
Such interactions fit in the latter category with the creation of accounts,
assets, or contracts. 

Create an instance of ``UplinkJsonRpc`` client and connect directly to the
Uplink ledger to query data such as getting available blocks, peers, accounts,
assets, contracts.

```python
from uplink import *

rpc = UplinkJsonRpc()

# queries
print rpc.uplink_blocks()
print rpc.uplink_peers()
print rpc.uplink_accounts()
print rpc.uplink_assets()
print rpc.uplink_accounts()

```

More specific type of queries can be made by passing an address of a particular
account, asset, or contract.

```python
asset_addr = 'asset_address'
asset = rpc.uplink_get_asset(asset_addr)
print asset

account_addr = 'account_address'
account = rpc.uplink_get_account(account_addr)
print account

contract_addr = 'contract_address'
contract = rpc.uplink_get_contract(contract_addr)
print contract

```

#### Create Account

When creating an account, several parameters are required. This includes a
public key, metadata, and timezone. ``from_address`` is an associated account
that creates a new child account. It isn't required when creating an intial
first account. It can be set as ``None`` and an address will be derived from the
newly created public key.

```python
  # create a new public and private key 
  pubkey, skey = ecdsa_new()

  # set the active private key used to sign transaction headers
  rpc.uplink_set_key(skey)

  # create metadata to associate to account
  metadata = dict(stuff="key", bax="foo", fax="bar")

  # Create initial account
  new_acct = rpc.uplink_create_account(
      from_address=None, new_pubkey=pubkey, metadata=metadata, timezone="GMT" )

  # Or Create child account 
  from_addr = 'parent_account_address'
  new_acct = rpc.uplink_create_account(
      from_address=from_addr new_pubkey=pubkey, metadata=metadata, timezone="GMT")

  print(new_acct)
```


#### Create Asset

There are several fields associated with creating an asset. The name of asset
can be a general name or security identifier. The supply of an asset describes
the fungible quantity that will be available on the chain.  The ``asset_type``
determines if the type of asset is discrete (integer), fractional (fixed point),
or binary (boolean).  ``from_address``  and ``issuer`` are be the same
account address of the account creating the asset.  ``Precision`` is only
required when the ``asset_type`` is fractional and denotes the  decimal
precision of the number.

```python

from_address = "account_address_creating_asset"
name = 'test'
supply = 10000
asset_type = bytes("Discrete")
reference = "Token"
issuer = "should_be_same_as_from_address"
precision = None

new_asset = rpc.uplink_create_asset(
    from_address, name, supply, asset_type, reference, issuer, precision)

print new_asset
```

Documentation
------------


To learn more about the SDK please visit the
[documentation](https://www.adjoint.io/docs/sdks.html)

License
-------

Copyright 2017 Adjoint Inc

Released under Apache 2.0.

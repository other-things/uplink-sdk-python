# Basic example

This is a guided example that shows how to use the python sdk to interact with uplink.
It's also a summary of what is already explained in the [Readme](https://github.com/adjoint-io/uplink-sdk-python).
More extensive documentation can be found in our [docs page](https://adjoint.io/docs)

The goal is to create account, assets and contracts, and transfer assets between accounts, while querying the state of the ledger.

All the commands used in this document are summarized in `basic-example.py`, which can be run with `python ./basic-example.py`.

### 1. Run an Uplink node

Running an uplink node is throughly explained in Uplink's [Readme](https://github.com/adjoint-io/uplink):

In short, there are two options for running a new node with a fresh state:
- Using the haskell tool `stack` :
```
$ stack build
$ stack exec uplink -- chain init -c config/node.config.local -b "leveldb://uplink" -d node1 -p 8001 --rpc-port 8545 -v -k config/validators/auth0/key
```
- Using the uplink binary (see [releases](https://github.com/adjoint-io/uplink/releases)):
```
$ uplink chain init -c config/node.config.local -b "leveldb://uplink" -d node -p 8001 --rpc-port 8545 -v -k config/validators/auth0/key
```

As you can see, the node we are running exposes port `8545`. We will send our RPC commands to that port.

We are using leveldb in this example as our backend, but postgres is also supported.

### 2. Setup

In the root directory, install all dependencies of this project:
```
$ pipenv shell
$ pipenv install
```

Go to the `./examples` folder and open the python repl.
```
$ cd ./examples
$ python
```

We are ready to import our Uplink client.

```python
from uplink import *

rpc = UplinkJsonRpc("localhost", 8545)
```

### 3. Create accounts

We create accounts for two users, Alice and Bob, as follows:

Alice's account:
```python
alice_pk, alice_sk = ecdsa_new()
alice_create_account_tx, alice_account_addr = rpc.uplink_create_account(
        private_key=alice_sk,
        public_key=alice_pk,
        from_address=None,
        metadata={'Name': 'Alice'},
        timezone="GMT"
    )
```

Bob's account:
```python
bob_pk, bob_sk = ecdsa_new()
bob_create_account_tx, bob_account_addr = rpc.uplink_create_account(
        private_key=bob_sk,
        public_key=bob_pk,
        from_address=None,
        metadata={'Name': 'Bob'},
        timezone="GMT"
    )
```

### 4. Create assets

Let Alice create a new asset and call it "USD".
The supply of an asset describes the fungible quantity that will be available on the chain.

```python
usd_asset_name = "USD"
supply = 10000
usd_asset_tx, usd_asset_address = rpc.uplink_create_asset(
        private_key=alice_sk,
        origin=alice_account_addr,
        name=usd_asset_name,
        supply=supply,
        asset_type_nm="Discrete",
        reference="Token",
        issuer=alice_account_addr,
    )
```

### 5. Query state of the ledger

We want to make sure our accounts and assets have been created.

```python
all_accounts = rpc.uplink_accounts()
all_assets = rpc.uplink_assets()
```

### 6. Circulate asset

The issuer of an asset needs to allocate the initial pool of the supply
so that the asset can be transferred among the parties in the system.
Holdings in uplink are explained carefully [here](https://www.adjoint.io/docs/assets.html#holdings)

```python
allocated_supply = supply * 0.75
usd_circulated_tx = rpc.uplink_circulate_asset(alice_sk, alice_account_addr, allocated_supply, usd_asset_address)
```

Now Alice has 7500 holdings of asset USD that she can transfer.

### 7. Transfer assets

Let's make Alice transfer some of her holdings to Bob.

```python
transfer_amount = 0.4 * allocated_supply
results = rpc.uplink_transfer_asset(
                private_key=alice_sk,
                from_address=alice_account_addr,
                to_address=bob_account_addr,
                balance=transfer_amount,
                asset_address=usd_asset_address)
```

We can now check that holdings have been transferred.

```python
usd_updated_asset = rpc.uplink_get_asset(usd_asset_address)
usd_updated_asset.holdings
```

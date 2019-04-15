# -*- coding: utf-8 -*-

from .client import UplinkJsonRpc
from .exceptions import RpcConnectionFail, UplinkJsonRpcError
from .protocol import Account

class UplinkSession(object):
    """JSON RPC session instance"""

    def __init__(self, addr=None, port=None):
        self.addr = addr or '127.0.0.1'
        self.port = port or 8545
        self.conn = None
        self.base = None
        self.app = None
        self.RpcConnectionFail = RpcConnectionFail
        self.UplinkJsonRpcError = UplinkJsonRpcError

    def init_app(self, app):
        """Connect application instance to uplink session"""
        app.extensions = getattr(app, 'extensions', {})
        self.app = app

        if app.config['TESTING'] is False:
            self._connect(app)
        else:
            # otherwise noop connection
            pass

    def _connect(self, app):
        print(self.addr, self.port)
        self.conn = UplinkJsonRpc(self.addr, self.port)

    def block(self, block_id=0):
        """Get specific block in chain"""
        block = self.conn.uplink_block(block_id)
        return block

    def blocks(self):
        """Get blocks in chain"""
        blockset = self.conn.uplink_blocks()
        return blockset

    def peers(self):
        """All Peer information"""
        peers = self.conn.uplink_peers()
        return peers

    def validators(self):
        """All Validators information"""
        valids = self.conn.uplink_validators()
        return valids

    def transactions(self, block_id=0):
        """Get All transactions by block index"""
        tx = self.conn.uplink_transactions(block_id)
        return tx

    def get_transaction_status(self, tx_hash):
        """Get a transaction status"""
        status = self.conn.uplink_get_transaction_status(tx_hash)
        return status

    def accounts(self):
        """Get All Accounts"""
        accounts = self.conn.uplink_accounts()
        return accounts

    def getaccount(self, address):
        """Get Specific Account"""
        account = self.conn.uplink_get_account(address)
        return account

    # Warning: Does not verify that the account was created in Uplink.
    def create_account_qr(self, new_pubkey, from_address=None, metadata=None, timezone=None):
        """Create New Account"""
        from .cryptography import make_qrcode
        (tx_hash, address) = self.conn.uplink_create_account(
            new_pubkey, from_address, metadata, timezone)
        pubkey_qr = make_qrcode(new_pubkey, 'pubkey')
        addr_qr = make_qrcode(address, 'addr')
        account = Account(timezone, new_pubkey, metadata, address)
        return account, pubkey_qr, addr_qr

    # Warning: Does not verify that the account was created in Uplink.
    def create_account(self, private_key, public_key, from_address=None, metadata=None, timezone=None):
        """Create New Account"""
        (tx_hash, address) = self.conn.uplink_create_account(private_key, public_key, from_address, metadata, timezone)
        account = Account(timezone, public_key, metadata, address)
        return account

    def assets(self):
        """Get All Assets"""
        assets = self.conn.uplink_assets()
        return assets

    def getasset(self, address):
        """Get Specific Asset"""
        return self.conn.uplink_get_asset(address)

    def create_asset(self, private_key, origin, name, supply, asset_type, reference, issuer, precision=None):
        """Create New Asset"""
        new_asset = self.conn.uplink_create_asset(
            private_key, origin, name, supply, asset_type, reference, issuer, precision)
        return new_asset

    def contracts(self):
        """Get All Contracts"""
        contracts = self.conn.uplink_contracts()
        return contracts

    def getcontract(self, address):
        """Get Specific Contract"""
        return self.conn.uplink_get_contract(address)

    def get_contract_callable(self, address):
        """Get Specific Contract"""
        return self.conn.uplink_get_contract_callable(address)

    def create_contract(self, private_key, from_address, script):
        """Create New Contract"""
        new_contract = self.conn.uplink_create_contract(
            private_key, from_address, script)
        return new_contract

    def validate_script(self, content):
        """Validate script"""
        validated_script = self.conn.uplink_validate_script(content)
        return validated_script

    def parse_script(self, content):
        """Parse script"""
        parsed_script = self.conn.uplink_parse_script(content)
        return parsed_script

    def validate_method(self, content):
        """Validate method"""
        return self.conn.uplink_validate_method(content)

    def validate_def(self, content):
        """Validate def"""
        return self.conn.uplink_validate_def(content)

    def command(self, content):
        """Adjoint command"""
        return self.conn.uplink_command(content)

    def transfer_asset(self, private_key, from_address, to_address, balance, asset_address):
        """Transfer asset"""
        receipt = self.conn.uplink_transfer_asset(
            private_key, from_address, to_address, balance, asset_address)
        return receipt

    def circulate_asset(self, private_key, from_address, amount, asset_address):
        """Circulate asset"""
        receipt = self.conn.uplink_circulate_asset(
            private_key, from_address, amount, asset_address)
        return receipt

    def get_invalid_transactions(self):
        """Get list of invalid transactions"""
        txs = self.conn.uplink_get_invalid_transactions()
        return txs

    def get_invalid_transaction(self, tx_hash):
        """Get an invalid transaction"""
        tx = self.conn.uplink_get_invalid_transaction(tx_hash)
        return tx

    def get_mempool(self):
        """Get list of unconfirmed transactions"""
        pool = self.conn.uplink_get_mempool()
        return pool

    def version(self):
        return self.conn.uplink_version()

    def test_saturate_network(self, n_txs, n_secs):
        return self.conn.uplink_test_saturate_network(n_txs, n_secs)

    def revoke_account(self, private_key, from_address, account_addr):
        """Revoke Account"""
        rev = self.conn.uplink_revoke_account(
            private_key, from_address, account_addr)
        return rev

    def revoke_asset(self, private_key, from_address, asset_addr):
        """Revoke Asset"""
        rev_asset = self.conn.uplink_revoke_asset(
            private_key, from_address, asset_addr)
        return rev_asset

    def call_contract(self, private_key, from_address, contract_addr, method, args):
        """Call Contract Methods"""
        called = self.conn.uplink_call_contract(
            private_key, from_address, contract_addr, method, args)
        return called

    def reset_db(self, public_key, private_key):
        """Reset Uplink Database"""
        reset = self.conn.uplink_reset_db(private_key, public_key)
        return reset

    def query(self, query):
        """Query Uplink Database"""
        response = self.conn.uplink_query(query)
        return response

    def create_sim(self, script, world=None):
        """Create Simulation"""
        return self.conn.uplink_create_sim(script)

    def update_sim_set_time(self, timestamp):
        """Update Simulation - Set Timestamp"""
        return self.conn.uplink_update_sim_set_time(timestamp)

    def update_sim_call_method(self, method, args):
        """Update Simulation - Call Contact Method"""
        return self.conn.uplink_update_sim_call_method(method, args)

    def query_sim_methods(self, contract_addr):
        """Query Simulation Contract Methods"""
        return self.conn.upink_query_sim_methods(contract_addr)

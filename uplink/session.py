# -*- coding: utf-8 -*-

from .client import UplinkJsonRpc
from .exceptions import RpcConnectionFail, UplinkJsonRpcError


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

    def blocks(self, count=1):
        """Get blocks in chain"""
        blockset = self.conn.uplink_blocks(count)
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

    def accounts(self):
        """Get All Accounts"""
        accounts = self.conn.uplink_accounts()
        return accounts

    def getaccount(self, address):
        """Get Specific Account"""
        account = self.conn.uplink_get_account(address)
        return account

    def create_account_qr(self, new_pubkey, from_address=None, metadata=None, timezone=None):
        """Create New Account"""
        from .cryptography import make_qrcode
        newaccount = self.conn.uplink_create_account(
            new_pubkey, from_address, metadata, timezone)
        pubkey = newaccount.public_key
        addr = newaccount.address

        pubkey_qr = make_qrcode(pubkey, 'pubkey')
        addr_qr = make_qrcode(addr, 'addr')

        return newaccount, pubkey_qr, addr_qr

    def create_account(self, private_key, public_key, from_address=None, metadata=None, timezone=None):
        """Create New Account"""
        newaccount = self.conn.uplink_create_account(private_key, public_key,
                                                     from_address, metadata, timezone)
        return newaccount

    def assets(self):
        """Get All Assets"""
        assets = self.conn.uplink_assets()
        return assets

    def getasset(self, address):
        """Get Specific Asset"""
        return self.conn.uplink_get_asset(address)

    def create_asset(self, private_key, origin, name, supply, asset_type, reference, issuer, precision=0):
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

    def create_contract(self, private_key, from_address, script):
        """Create New Contract"""
        new_contract = self.conn.uplink_create_contract(
            private_key, from_address, script)
        return new_contract

    def transfer_asset(self, private_key, from_address, to_address, balance, asset_address):
        """Transfer asset"""
        receipt = self.conn.uplink_transfer_asset(
            private_key, from_address, to_address, balance, asset_address)
        return receipt

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

    def call_contract(self, private_key, from_address, contract_addr, method, args):
        """Call Contract Methods"""
        called = self.conn.uplink_call_contract(
            private_key, from_address, contract_addr, method, args)
        return called

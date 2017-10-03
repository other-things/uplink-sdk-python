# -*- coding: utf-8 -*-

import json
import time
import codecs
import requests

from requests.exceptions import ConnectionError as RequestsConnectionError
from .protocol import (Block, Peer, Account, Asset, Assets, Contract, Transaction,
                       MemPool, Transfer, TxAccount, TxAsset, TxContract, CreateAccount,
                       CreateAsset, CreateContract, RevokeAccount, Call, SyncLocal, Bind,
                       CreateAccountHeader, CreateAssetHeader, TransferAssetHeader,
                       CreateContractHeader, RevokeAccountHeader, CallHeader, BindHeader, SyncHeader)
from .exceptions import (RpcConnectionFail, BadStatusCodeError, BadJsonError,
                         BadResponseError, UplinkJsonRpcError)
from .cryptography import (pack_signature,
                           get_time,
                           derive_contract_address,
                           derive_account_address,
                           derive_asset_address)

UPLINK_PORT = 8545


class UplinkJsonRpc(object):
    """JSON RPC For Uplink"""

    def __init__(self, host='localhost', port=UPLINK_PORT, tls=False, endpoint=None, privkey=None, pubkey=None):
        self.host = host
        self.port = port
        self.endpoint = endpoint
        self.tls = tls

    def _call(self, method, params=None, endpoint=None):
        self.endpoint = endpoint
        params = params or {}
        data = {
            'method': method,
            'params': params,
        }
        scheme = 'http'
        if self.tls:
            scheme += 's'
        if self.endpoint is None:
            url = '{}://{}:{}'.format(scheme, self.host, self.port)
        else:
            url = '{}://{}:{}/{}'.format(scheme, self.host,
                                         self.port, self.endpoint)

        try:
            req = requests.post(url, data=json.dumps(data))
        except RequestsConnectionError:
            raise RpcConnectionFail('connection error:', None)
        if req.status_code / 100 != 2:
            raise BadStatusCodeError("status code: ", req.status_code)
        try:
            response = req.json()
        except ValueError:
            raise BadJsonError("bad json error", req.error)
        try:
            return response
        except KeyError:
            raise BadResponseError("bad json error", response)

    def _handle_response(self, result, many=True, contracts=False):
        if result['tag'] == "RPCResp":
            if many:
                assert type(result['contents']) is list
            else:
                assert type(result['contents']) is dict
            return result['contents']
        else:
            if contracts:
                return result['contents']
            else:
                raise UplinkJsonRpcError("Malformed Response", result)

    def _handle_success(self, result):
        if result['tag'] == "RPCRespOK":
            return True
        else:
            return False

    def uplink_block(self, block_id):
        """Get a block by index"""
        block_by_id = 'blocks/{}'.format(block_id)
        result = self._call('GET', endpoint=block_by_id)
        elems = self._handle_response(result, many=False)
        return Block(**elems)

    def uplink_blocks(self, count=1):
        """Get a list of blocks"""
        result = self._call('GET', endpoint='blocks')
        elems = self._handle_response(result, many=True)
        return [Block(**args) for args in elems]

    def uplink_peers(self):
        """Get a list of peers and return number of peers"""
        result = self._call('GET', endpoint='peers')
        elems = self._handle_response(result, many=True)
        return [Peer(**args) for args in elems]

    def uplink_validators(self):
        """Get a list of peers and return number of validating peers"""
        result = self._call('GET', endpoint='peers/validators')
        elems = self._handle_response(result, many=True)
        return [Peer(**args) for args in elems]

    def uplink_transactions(self, block_id=0):
        """Get a list of transactions by block index"""
        transactions_by_id = 'transactions/{}'.format(block_id)
        result = self._call('GET', endpoint=transactions_by_id)
        elems = self._handle_response(result, many=True)
        print(elems)
        for arg in elems:
            return [Transaction(**args) for args in elems]

    def uplink_accounts(self):
        """Get a list of accounts"""
        result = self._call('GET', endpoint='accounts')
        elems = self._handle_response(result, many=True)
        return [Account(**args) for args in elems]

    def uplink_get_account(self, address):
        """Get individual account by address [/accounts/<address>]"""
        account_by_address = 'accounts/{}'.format(address)
        result = self._call('GET', endpoint=account_by_address)
        elems = self._handle_response(result, many=False)
        return Account(**elems)

    def uplink_assets(self):
        """Get a list of assets"""
        result = self._call('GET', endpoint='assets')
        elems = self._handle_response(result, many=True)

        return [Assets(**args) for args in elems]

    def uplink_get_asset(self, address):
        """Get individual asset by address [/assets/<address>]"""
        asset_by_address = 'assets/{}'.format(address)
        result = self._call('GET', endpoint=asset_by_address)
        elems = self._handle_response(result, many=False)
        try:
            if elems['errorMsg']:
                print(elems['errorMsg'])
                return False
        except KeyError:
            return Asset(address=address, **elems)

    def uplink_version(self):
        return self._call('GET', endpoint='version')

    def uplink_contracts(self):
        """Get a list of contacts"""
        result = self._call('GET', endpoint='contracts')
        elems = self._handle_response(result, many=True, contracts=True)

        return [Contract(**args) for args in elems]

    def uplink_get_contract(self, address):
        """Get individual contract by address [/contracts/<address>]"""
        contract_by_address = 'contracts/{}'.format(address)
        result = self._call('GET', endpoint=contract_by_address)
        elems = self._handle_response(result, many=False, contracts=False)
        return Contract(**elems)

    def uplink_get_mempool(self):
        """Get list of unconfirmed transactions"""
        result = self._call('GET', endpoint='transactions/pool')
        mem_pool_dict = self._handle_response(result, many=False)
        return MemPool(mem_pool_dict)

    def uplink_get_mempool_size(self):
        """Get size of node mempool"""
        result = self._call('GET', endpoint='transactions/pool/size')
        return self._handle_response(result, many=False)

    def uplink_get_mempools(self):
        """Get unconfirmed transactions of all nodes in the network"""
        return self._call('GET', endpoint='transactions/pool/all')

    def uplink_get_mempools_sizes(self):
        """Get size of mempool for all nodes in the network"""
        return self._call('GET', endpoint='transactions/pool/all/sizes')

    def uplink_test_saturate_network(self, n_txs, n_secs):
        """Send cmd to p2p network to spawn n txs over m seconds"""
        params = {
            "method": "SaturateNetwork",
            "params": {"nTxs": n_txs,
                       "nSecs": n_secs}
        }
        # this request will return an error if the node is not in test mode
        return self._call("Test", params)

    def uplink_test_reset_mempools(self):
        """Send cmd to p2p network to reset all mempools of all nodes"""
        params = {
            "method": "ResetMemPools",
            "params": {}
        }
        # this request will return an error if the node is not in test mode
        return self._call("Test", params)

    def uplink_create_account(self, private_key, public_key,
                              from_address=None, metadata=None, timezone=None, nodekey=0):
        """Create new account"""
        if timezone is None:
            timezone, localtz = time.tzname

        timestamp = get_time()

        pubkey = public_key.to_string()
        public_key_hex = codecs.encode(pubkey, 'hex')

        acc_address = derive_account_address(public_key)

        hdr = CreateAccountHeader(
            public_key_hex, metadata, acc_address, timezone, nodekey)
        txb = TxAccount(CreateAccount(hdr))

        r, s = hdr.sign(private_key)
        signature = pack_signature(r, s)

        origin = acc_address if from_address is None else from_address
        tx = Transaction(txb, signature, timestamp,
                         origin=origin, to=acc_address)

        params = tx.to_dict()

        result = self._call('Transaction', params=params, endpoint='')

        if self._handle_success(result):
            return Account(timezone, public_key, metadata, nodekey, acc_address)
        else:
            raise UplinkJsonRpcError("Malformed CreateAccount", result)

    def uplink_create_asset(self, private_key, origin, name,
                            supply, asset_type, reference, issuer, precision=0):
        """Create Asset - returns (result, to_address)"""
        timestamp = get_time()

        hdr = CreateAssetHeader(name, supply, asset_type,
                                reference, issuer, precision)
        txb = TxAsset(CreateAsset(hdr))

        r, s = hdr.sign(private_key)
        signature = pack_signature(r, s)

        to_address = derive_asset_address(r, s, timestamp, issuer)

        tx = Transaction(txb, signature, timestamp,
                         origin=origin, to=to_address)
        params = tx.to_dict()

        result = self._call('Transaction', params=params, endpoint='')

        if self._handle_success(result):
            return (result, to_address)
        else:
            raise UplinkJsonRpcError("Malformed CreateAsset", result)

    def uplink_transfer_asset(self, private_key, from_address, to_address, balance, asset_address):
        """Transfer assets"""
        timestamp = get_time()

        hdr = TransferAssetHeader(asset_address, to_address, balance)
        txb = TxAsset(Transfer(hdr))

        r, s = hdr.sign(private_key)
        signature = pack_signature(r, s)

        tx = Transaction(txb, signature.decode(), timestamp,
                         origin=from_address, to=None)
        params = tx.to_dict()
        result = self._call('Transaction', params=params, endpoint='')
        if self._handle_success(result):
            return result
        else:
            raise UplinkJsonRpcError("Malformed TransferAsset", result)

    def uplink_create_contract(self, private_key, from_address, script):
        """Create a new Contract"""
        timestamp = get_time()

        raw_addr = derive_contract_address(timestamp, script)

        hdr = CreateContractHeader(
            script, from_address, raw_addr,
            timestamp, storage=None, methods=None)
        txb = TxContract(CreateContract(hdr))

        r, s = hdr.sign(private_key)
        signature = pack_signature(r, s)

        tx = Transaction(txb, signature, timestamp,
                         origin=from_address, to=raw_addr)
        params = tx.to_dict()

        result = self._call('Transaction', params=params, endpoint='')
        if self._handle_success(result):
            return result, raw_addr
        else:
            raise UplinkJsonRpcError("create contract error", result)

    def uplink_revoke_account(self, private_key, from_address, account_addr):
        """Revoke account access"""
        timestamp = get_time()

        hdr = RevokeAccountHeader(account_addr)
        txb = TxAccount(RevokeAccount(hdr))

        r, s = hdr.sign(private_key)
        signature = pack_signature(r, s)

        # to_address=to_address)
        tx = Transaction(txb, signature, timestamp, origin=from_address)
        params = tx.to_dict()

        result = self._call('Transaction', params=params, endpoint='')
        if self._handle_success(result):
            return result
        else:
            raise UplinkJsonRpcError("Malformed RevokeAccount", result)

    def uplink_bind_asset(self, private_key, from_address, contract_addr, asset_addr):
        """Bind asset to a contract"""
        timestamp = get_time()

        hdr = BindHeader(contract_addr, asset_addr)
        txb = TxAsset(Bind(hdr))

        r, s = hdr.sign(private_key)
        signature = pack_signature(r, s)

        # XXX Not implemented yet.
        # to_address = derive_contract_address()

        tx = Transaction(txb, signature, timestamp,
                         origin=from_address)  # to_address=to_address)
        params = tx.to_dict()

        result = self._call('Transaction', params=params, endpoint='')

        if self._handle_success(result):
            return result
        else:
            raise UplinkJsonRpcError("Malformed BindAsset", result)

    def uplink_call_contract(self, private_key, from_address, contract_addr, method, args):
        """Call contract method"""
        timestamp = get_time()

        hdr = CallHeader(contract_addr, method, args)
        txb = TxContract(Call(hdr))

        r, s = hdr.sign(private_key)
        signature = pack_signature(r, s)

        tx = Transaction(txb, signature, timestamp,
                         origin=from_address)  # to_address=to_address)
        params = tx.to_dict()

        result = self._call('Transaction', params=params, endpoint='')

        if self._handle_success(result):
            return result
        else:
            raise UplinkJsonRpcError("Malformed CallContract", result)

    def uplink_sync_local(self, private_key, from_address, contract_addr):
        """Sync local contract storage"""
        timestamp = get_time()

        hdr = SyncHeader(contract_addr)
        txb = TxContract(SyncLocal(hdr))

        r, s = hdr.sign(private_key)
        signature = pack_signature(r, s)

        tx = Transaction(txb, signature, timestamp,
                         origin=from_address)  # to_address=to_address)
        params = tx.to_dict()

        result = self._call('Transaction', params=params, endpoint='')

        if self._handle_success(result):
            return result
        else:
            raise UplinkJsonRpcError("Malformed SyncLocal", result)

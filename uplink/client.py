# -*- coding: utf-8 -*-

import json
import time
import codecs
import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from .protocol import (Block, Peer, Account, Asset, Contract, Transaction,
                       MemPool, Transfer, TxAccount, TxAsset, TxContract, CreateAccount,
                       CreateAsset, CreateContract, RevokeAccount, Call, SyncLocal, Bind,
                       CreateAccountHeader, CreateAssetHeader, TransferAssetHeader, Circulate, CirculateAssetHeader, AssetType,
                       CreateContractHeader, RevokeAccountHeader, RevokeAsset, RevokeAssetHeader, CallHeader, BindHeader, SyncHeader)
from .exceptions import (RpcConnectionFail, BadStatusCodeError, BadJsonError,
                         BadResponseError, UplinkJsonRpcError,
                         TransactionNonExistent)
from .cryptography import (pack_signature,
                           get_time,
                           derive_contract_address,
                           derive_account_address,
                           derive_asset_address,
                           ecdsa_sign)

UPLINK_PORT = 8545


class UplinkJsonRpc(object):
    """JSON RPC For Uplink"""

    def __init__(self, host='localhost', port=UPLINK_PORT, tls=False, endpoint=None, privkey=None, pubkey=None):
        self.host = host
        self.port = port
        self.endpoint = endpoint
        self.tls = tls

    def _make_url(self, endpoint):
        scheme = 'https' if self.tls else 'http'
        #  if endpoint is None:
            #  return '{}://{}:{}'.format(scheme, self.host, self.port)
        #  else:
        return '{}://{}:{}/{}'.format(scheme, self.host,
                                         self.port, endpoint)

    def _make_cmd_data(self, method, params={}):
        data = {
            'method': method,
            'params': params,
        }
        return json.dumps(data)


    def _call(self, data='', method='post', params={}, endpoint=''):
        url = self._make_url(endpoint)

        try:
            req = getattr(requests, method)(url, data=data)
        except RequestsConnectionError:
            raise RpcConnectionFail('connection error:', None)
        if req.status_code / 100 != 2:
            raise BadStatusCodeError("status code: ", req.status_code)
        try:
            response = req.json()
        except ValueError:
            raise BadJsonError("bad json error", req.error)

        return response

    # Issues a transaction to the uplink RPC interface, returning the
    # tranasction hash on success, and throwing an exception on failure.
    def _issue_transaction(self, tx):
        data = self._make_cmd_data("Transaction", tx.to_dict())
        response = self._call(data)
        if response["tag"] == "RPCTransactionOK":
            return response["txHash"]
        else:
            print(response)
            raise UplinkJsonRpcError("Malformed Transaction: " + str(tx), response)

    def _handle_response(self, result, many=True):
        if result['tag'] in ["RPCResp", "RPCTransactionOK"]:
            if many:
                assert type(result['contents']) is list
            else:
                assert type(result['contents']) is dict
            return result['contents']
        else:
            print(result)
            raise UplinkJsonRpcError(result["tag"], result["contents"])

    def _handle_success(self, result):
        if result['tag'] in ["RPCRespOK", "RPCTransactionOK"]:
            return True
        else:
            return False

    def uplink_reset_db(self, private_key, public_key):
        """
        Resets and clears Uplink database.
        This request will return an error if the node is not in test mode

        :param private_key: private key of primary account
        :param public_key: public key of primary account
        """
        address = derive_account_address(public_key)
        r, s = ecdsa_sign(private_key, address)
        signature = pack_signature(r, s)

        params = {
            "method": "ResetDB",
            "params": {
                "address": address,
                "signature": signature
            }
        }

        return self._call(self._make_cmd_data("Test", params))

    def uplink_block(self, block_id):
        """
        Get a block by index

        :param block_id:
        :return: specific block
        """
        block_by_id = 'blocks/{}'.format(block_id)
        result = self._call(endpoint=block_by_id)
        elems = self._handle_response(result, many=False)
        return Block(**elems)

    def uplink_blocks(self):
        """
        Get a list of all blocks

        :return: all blocks
        """
        result = self._call(endpoint='blocks')
        elems = self._handle_response(result, many=True)
        return [Block(**args) for args in elems]

    def uplink_peers(self):
        """
        Get a list of peers and return number of peers

        :return: all peers
        """
        result = self._call(endpoint='peers')
        elems = self._handle_response(result, many=True)
        return [Peer(**args) for args in elems]

    def uplink_validators(self):
        """
        Get a list of peers and return number of validating peers

        :return: all validating peers
        """
        result = self._call(endpoint='peers/validators')
        elems = self._handle_response(result, many=True)
        return [Peer(**args) for args in elems]

    def uplink_get_transaction_status(self, tx_hash):
        """
        Get a transactions status

        :return:
        """
        response = self._call(endpoint='transactions/status/{}'.format(tx_hash))
        if response["contents"] == "NonExistent":
            raise TransactionNonExistent(tx_hash)
        else:
            return response["contents"]

    def uplink_transactions(self, block_id=0):
        """
        Get a list of transactions by block index

        :param block_id:
        :return: all transactions specified by block id
        """
        transactions_by_id = 'transactions/{}'.format(block_id)
        result = self._call(endpoint=transactions_by_id)
        elems = self._handle_response(result, many=True)
        return [Transaction(**args) for args in elems]

    def uplink_accounts(self):
        """
        Get a list of accounts

        :return: all accounts
        """
        result = self._call(endpoint='accounts')
        elems = self._handle_response(result, many=True)
        return [Account(**args) for args in elems]

    def uplink_get_account(self, address):
        """
        Get individual account by address [/accounts/<address>]

        :param address: account address
        :return: specific account and associated details
        """
        account_by_address = 'accounts/{}'.format(address)
        result = self._call(endpoint=account_by_address)
        elems = self._handle_response(result, many=False)
        return Account(**elems)

    def uplink_assets(self):
        """
        Get a list of all assets

        :return: all assets
        """
        result = self._call(endpoint='assets')
        elems = self._handle_response(result, many=True)

        return [Asset(**args) for args in elems]

    def uplink_get_asset(self, address):
        """
        Get individual asset by address [/assets/<address>]

        :param address: asset address
        :return: specific asset and associated details
        """
        asset_by_address = 'assets/{}'.format(address)
        result = self._call(endpoint=asset_by_address)
        elems = self._handle_response(result, many=False)
        try:
            if elems['errorMsg']:
                print(elems['errorMsg'])
                return False
        except KeyError:
            return Asset(**elems)

    def uplink_version(self):
        """
        Get current Uplink version

        :return: version
        """
        return self._call(endpoint='version')

    def uplink_contracts(self):
        """
        Get a list of all contacts

        :return: all contracts
        """
        result = self._call(endpoint='contracts')
        elems = self._handle_response(result, many=True)

        return [Contract(**args) for args in elems]

    def uplink_get_contract(self, address):
        """
        Get individual contract by address

        :param address: contract address
        :return: specific contract and associated details
        """
        contract_by_address = 'contracts/{}'.format(address)
        result = self._call(endpoint=contract_by_address)
        elems = self._handle_response(result, many=False)
        return Contract(**elems)

    def uplink_get_contract_callable(self, address):
        """
        Get individual contract methods by address
        return specific contract methods
        """
        contract_by_address = 'contracts/{}/callable'.format(address)
        result = self._call(endpoint=contract_by_address)
        elems = self._handle_response(result, many=False)
        return elems

    def uplink_validate_script(self, content):
        """
        Validate a contract
        :return: errors or a compiled contract
        """
        endpoint = "scripts/validate"
        response = self._call(content, endpoint=contract_by_address)
        return self._handle_response(response, many=False)

    def uplink_command(self, payload):
        """

        """
        endpoint = "scripts/command"
        response = self._call(json.dumps(payload), endpoint=endpoint)
        return self._handle_response(response, many=False)

    def uplink_get_invalid_transaction(self, tx_hash):
        """
        Get a transactions status

        :return:
        """
        response = self._call(endpoint='transactions/invalid/{}'.format(tx_hash))
        if response["contents"] == "NonExistent":
            raise TransactionNonExistent(tx_hash)
        else:
            return response["contents"]

    def uplink_get_invalid_transactions(self):
        """
        Get list of invalid transactions

        :return: all invalid transactions
        """
        result = self._call(endpoint='transactions/invalid')
        elems = self._handle_response(result, many=True)
        return elems

    def uplink_get_mempool(self):
        """
        Get list of unconfirmed transactions

        :return: all unconfirmed transactions on current node
        """
        result = self._call(endpoint='transactions/pool')
        mem_pool_dict = self._handle_response(result, many=False)
        return MemPool(mem_pool_dict)

    def uplink_get_mempool_size(self):
        """
        Get size of node mempool
        :return: amount of unconfirmed transactions on current node
        """
        result = self._call(endpoint='transactions/pool/size')
        return self._handle_response(result, many=False)

    def uplink_get_mempools(self):
        """
        Get unconfirmed transactions of all nodes in the network.

        :return: amount of unconfirmed
        """
        return self._call(endpoint='transactions/pool/all')

    def uplink_get_mempools_sizes(self):
        """
        Get size of mempool for all nodes in the network.

        :return: amount of unconfirmed transactions on all network nodes
        """
        return self._call(endpoint='transactions/pool/all/sizes')

    def uplink_test_saturate_network(self, n_txs, n_secs):
        """
        Send cmd to p2p network to spawn n txs over m seconds.
        This request will return an error if the node is not in test mode

        :param n_txs: number of transactions to send
        :param n_secs: number of seconds to send those transactions in
        """
        params = {
            "method": "SaturateNetwork",
            "params": {"nTxs": n_txs,
                       "nSecs": n_secs}
        }
        return self._call(self._make_cmd_data("Test", params))

    def uplink_test_reset_mempools(self):
        """
        Send cmd to p2p network to reset all mempools of all nodes.
        This request will return an error if the node is not in test mode

        :return: clears list of unconfirmed transactions on network
        """
        params = {
            "method": "ResetMemPools",
            "params": {}
        }
        return self._call(self._make_cmd_data("Test", params))

    def uplink_create_account(self, private_key, public_key,
                              from_address=None, metadata=None, timezone=None):
        """
        Create new account

        :param private_key: Private key of account to be created
        :param public_key: Public key of account to be created
        :param from_address: Address of account to be created
        :param metadata: Metadata to be associated with created account
        :param timezone: Timezone information related to account
        :return: account
        """
        if timezone is None:
            timezone, localtz = time.tzname
        if metadata is None:
            metadata = {}


        public_key_hex = codecs.encode(public_key.to_string(), 'hex')

        acc_address = derive_account_address(public_key)
        hdr = CreateAccountHeader(
            public_key_hex, metadata, acc_address, timezone)
        txb = TxAccount(CreateAccount(hdr))

        r, s = hdr.sign(private_key)
        signature = pack_signature(r, s)

        origin = acc_address if from_address is None else from_address
        tx = Transaction(txb, signature, origin=origin)

        tx_hash = self._issue_transaction(tx)
        return (tx_hash, acc_address)

    def uplink_create_asset(self, private_key, origin, name,
                            supply, asset_type_nm, reference, issuer,
                            precision=None, metadata=None):
        """
        Create Asset

        :param private_key: private key of account creating asset
        :param origin: address of account creating asset
        :param name: name of asset
        :param supply: amount of asset holdings to be created
        :param asset_type_nm: name of asset type: Discrete, Fractional, Binary
        :param reference: Token, Security, GBP, EUR, CHF, USD
        :param issuer: same as origin
        :param precision: decimal precision for Fractional assets only
        :return: tuple of transaction hash and asset address
        """
        """Create Asset - returns (result, to_address)"""

        if metadata is None:
            metadata = {}

        hdr = CreateAssetHeader(name, supply, asset_type_nm,
                                reference, issuer, precision, metadata)
        txb = TxAsset(CreateAsset(hdr))

        r, s = hdr.sign(private_key)
        signature = pack_signature(r, s)

        tx = Transaction(txb, signature, origin=origin)

        tx_hash = self._issue_transaction(tx)
        asset_address = derive_asset_address(tx_hash)
        return (tx_hash, asset_address)

    def uplink_transfer_asset(self, private_key, from_address, to_address, balance, asset_address):
        """
        Transfer Asset holdings

        :param private_key: private key of account transferring holdings
        :param from_address: address of account transferring holdings
        :param to_address: address holdings are being transferred to
        :param balance: amount of holdings to be transferred
        :param asset_address: address of asset to be transferred
        :return: transaction hash if successful
        """

        hdr = TransferAssetHeader(asset_address, to_address, balance)

        txb = TxAsset(Transfer(hdr))
        r, s = hdr.sign(private_key)
        signature = pack_signature(r, s)

        tx = Transaction(txb, signature, origin=from_address)

        tx_hash = self._issue_transaction(tx)
        return tx_hash

    def uplink_circulate_asset(self, private_key, from_address, amount, asset_address):
        """
        Circulate asset supply

        :param private_key: private key of account circulating asset
        :param from_address: address of account circulating asset
        :param amount: amount of asset holdings to be circulated
        :param asset_address: address of asset to be circulated
        :return: transaction hash if successful
        """
        hdr = CirculateAssetHeader(asset_address, amount)
        txb = TxAsset(Circulate(hdr))

        r, s = hdr.sign(private_key)
        signature = pack_signature(r, s)

        tx = Transaction(txb, signature, origin=from_address)

        tx_hash = self._issue_transaction(tx)
        return tx_hash

    def uplink_create_contract(self, private_key, from_address, script):
        """
        Create a new Contract

        :param private_key: private key of account creating contract
        :param from_address: address of account creating contract
        :param script: contract code
        :return: tuple of transaction hash and contract address
        """

        hdr = CreateContractHeader(script)
        txb = TxContract(CreateContract(hdr))

        r, s = hdr.sign(private_key)
        signature = pack_signature(r, s)

        tx = Transaction(txb, signature, origin=from_address)

        tx_hash = self._issue_transaction(tx)
        contract_address = derive_contract_address(tx_hash)
        return (tx_hash, contract_address)

    def uplink_revoke_asset(self, private_key, from_address, asset_addr):
        """
        Revoke Asset

        :param private_key: private key of account revoking asset - must be the same account as the initial issuer of the asset
        :param from_address: address of the account revoking asset
        :param asset_addr: address of the asset being revoked
        :return: transaction hash if successful
        """

        hdr = RevokeAssetHeader(asset_addr)
        txb = TxAsset(RevokeAsset(hdr))

        r, s = hdr.sign(private_key)
        signature = pack_signature(r, s)

        tx = Transaction(txb, signature, origin=from_address)

        tx_hash = self._issue_transaction(tx)
        return tx_hash

    def uplink_revoke_account(self, private_key, from_address, account_addr):
        """Revoke account access

        :param private_key: private key of account revoking access - must be the same account as the account being revoked
        :param from_address: address of account revoking access
        :param account_addr: address of the account being revoked
        :return: transaction hash if successful
        """

        hdr = RevokeAccountHeader(account_addr)
        txb = TxAccount(RevokeAccount(hdr))

        r, s = hdr.sign(private_key)
        signature = pack_signature(r, s)

        tx = Transaction(txb, signature, origin=from_address)

        tx_hash = self._issue_transaction(tx)
        return tx_hash

    def uplink_call_contract(self, private_key, from_address, contract_addr, method, args):
        """Call contract method

        :param private_key: private key of account calling contract method
        :param from_address: address of account calling contract method
        :param contract_addr: address of contract being called
        :param method: method name off contract being called
        :param args: arguments to the method
        :return: transaction hash if successful
        """

        hdr = CallHeader(contract_addr, method, args)
        txb = TxContract(Call(hdr))

        r, s = hdr.sign(private_key)
        signature = pack_signature(r, s)

        tx = Transaction(txb, signature, origin=from_address)

        tx_hash = self._issue_transaction(tx)
        return tx_hash

    def uplink_query(self, query):
        """Query Uplink Database - will only work if Uplink is created with postgres

        :param query: query string to send to database
        :return: response to query will be list of assets, accounts, or contracts.
        """
        result = self._call(self._make_cmd_data('Query', params=query))
        return self._handle_response(result, many=False)

    def uplink_sim_create(self, issuer, script, world=None):
        """Create Simulation"""
        params = {
            "tag": "CreateSimulationMsg",
            "contents": {
                "issuer": issuer,
                "fcl": script,
                "world": world
            }
        }
        result = self._call(self._make_cmd_data('Simulate', params=params))
        return self._handle_response(result, many=False)

    def uplink_sim_update(self, simulation_id, method_json):
        """
        Update Simulation

        :param simulation_id: The id of the simulated contract to update
        :param method_json: The dictionary representing the simulation update
        :return: RPCRespOK on success
        """
        params = {
            "tag": "UpdateSimulationMsg",
            "contents": {
                "simKey": simulation_id,
                "contents": method_json
            }
        }
        result = self._call(self._make_cmd_data('Simulate', params=params))
        if self._handle_success(result):
            return result
        else:
            print(result)
            raise UplinkJsonRpcError("Update Simulation failure:", result)

    # timestamp must be ISO_8601 formatted string
    def uplink_sim_update_set_time(self, simulation_id, timestamp):
        """
        Update Simulation - Set Timestamp

        :param simulation_id: The id of the simulated contract to set the timestamp of
        :param timestamp: The timestamp to set the contract's timestamp to
        :return: RPCRespOK on success
        """
        params = {
            "tag": "ModifyTimestamp",
            "contents": {
                "tag": "SetTimestamp",
                "contents": timestamp
            }
        }
        return self.uplink_sim_update(simulation_id, params)

    def uplink_sim_update_add_timedelta(self, simulation_id, delta_str):
        """
        Update Simulation - Add time delta

        :param simulation_id: The id of the simulated contract to increment the timestamp of
        :param delta_str: The string representing the timedelta to add to the contract's timestamp
        :return: RPCRespOK on success
        """
        params = {
            "tag": "ModifyTimestamp",
            "contents": {
                "tag": "AddTimeDelta",
                "contents": delta_str
            }
        }
        return self.uplink_sim_update(simulation_id, params)

    def uplink_sim_call(self, simulation_id, caller, method, args):
        """
        Update Simulation - Call Contact Method

        :param simulation_id: The id of the simulated contract to call a method
        :param method: The name of the contract method to call
        :param args: A list of arguments to pass to the method call
        """
        params = {
            "tag": "CallMethod",
            "contents": {
                "caller": caller,
                "methodName": method,
                "methodArgs": [arg.to_dict() for arg in args]
            }
        }
        return self.uplink_sim_update(simulation_id, params)

    def uplink_sim_query(self, simulation_id, query, addr=None, many=False):
        """
        Query Simulation

        :param simulation_id: The id of the simulated contract to query
        :param query: The name of the query to make
        :param addr: Address of specific value to query
        :param many: Whether or not to expect a list of items as a response
        :return: The result of the "query" specified
        """
        params = {
            "tag": "QuerySimulationMsg",
            "contents": {
                "simKey": simulation_id,
                "contents": {
                    "tag": query,
                    "contents": addr
                }
            }
        }
        result = self._call(self._make_cmd_data('Simulate', params=params))
        return self._handle_response(result, many=many)

    def uplink_sim_query_methods(self, simulation_id):
        """
        Query Simulation - Contract Methods

        :param simulation_id: The id of the simulated contract
        :return: The list of callable contract methods
        """
        return self.uplink_sim_query(simulation_id, "QueryMethods", many=True)

    def uplink_sim_query_contract(self, simulation_id):
        """
        Query Simulation Contract

        :param simulation_id: The id of the simulated contract
        :return: An Uplink Contract
        """
        res = self.uplink_sim_query(simulation_id, "QueryContract")

        error_val = res.get("errorMsg")
        if error_val:
            print(error_val)
            raise ValueError("Contract Simulation with id " + simulation_id + " does not exist")
        else:
            return Contract(**res)

    def uplink_sim_query_assets(self, simulation_id):
        """
        Query Simulation - Assets

        :param simulation_id: The id of the simulated contract
        :return: A list of assets in the simulated contract's environment
        """
        self.uplink_sim_query(simulation_id, "QueryAssets", many=True)

    def uplink_sim_query_asset(self, simulation_id, address):
        """
        Query Simulation - Asset

        :param simulation_id: The if of the simulated contract to query
        :param address: The address of the asset
        :return: An Uplink Asset
        """
        res = self.uplink_sim_query(simulation_id, "QueryAsset", address)

        error_val = res.get("errorMsg")
        if error_val:
            print(error_val)
            raise ValueError("Asset with address " + address + " does not exist")
        else:
            return Asset(**res)

class UplinkJsonRpcError(Exception):

    def __init__(self, message, response):
        self.message = message
        self.response = response

    def __repr__(self):
        return repr(self.message) + ":" + str(self.response)

class RpcConnectionFail(UplinkJsonRpcError):
    pass


class BadStatusCodeError(UplinkJsonRpcError):
    pass


class BadJsonError(UplinkJsonRpcError):
    pass


class BadResponseError(UplinkJsonRpcError):
    pass


class TransactionRejected(UplinkJsonRpcError):
    def __init__(self, tx_hash, status):
        self.tx_hash = tx_hash
        self.status = status


# This should only be raised when the SDK has issued a tranasaction but when it
# queries for the status of the transaction uplink responds with NonExistent
class TransactionNonExistent(UplinkJsonRpcError):
    def __init__(self, tx_hash):
        self.tx_hash = tx_hash

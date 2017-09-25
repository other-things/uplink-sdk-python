class UplinkJsonRpcError(Exception):

    def __init__(self, message, response):
        self.message = message
        self.response = response


class RpcConnectionFail(UplinkJsonRpcError):
    pass


class BadStatusCodeError(UplinkJsonRpcError):
    pass


class BadJsonError(UplinkJsonRpcError):
    pass


class BadResponseError(UplinkJsonRpcError):
    pass

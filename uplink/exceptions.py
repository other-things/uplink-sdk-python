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

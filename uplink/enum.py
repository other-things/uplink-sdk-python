# Transaction constructors
TxContract_name = "TxContract"
TxAsset_name = "TxAsset"
TxAccount_name = "TxAccount"

# TxContract constructors
CreateContract_name = "TxContract"
Call_name = "Call"

# TxAsset constructors
CreateAsset_name = "CreateAsset"
Transfer_name = "Transfer"
Circulate_name = "Circulate"
Bind_name = "Bind"
RevokeAsset_name = "RevokeAsset"

# TxAccount constructors
CreateAccount_name = "CreateAccount"
RevokeAccount_name = "RevokeAccount"

# Transaction Header should reflect TransactionHeader type in uplink
txHeader = [
    (TxContract_name, [CreateContract_name, Call_name]),
    (TxAsset_name, [CreateAsset_name, Transfer_name, Circulate_name, Bind_name, RevokeAsset_name]),
    (TxAccount_name, [CreateAccount_name, RevokeAccount_name])
]

def getFlags(fstConstr, sndConstr):
    fstFlag = [x[0] for x in txHeader].index(fstConstr)
    sndFlag = txHeader[fstFlag][1].index(sndConstr)
    return (fstFlag, sndFlag)

TxTypeCreateContract = getFlags(TxContract_name, CreateContract_name)
TxTypeCall = getFlags(TxContract_name, Call_name)
TxTypeCreateAsset = getFlags(TxAsset_name, CreateAsset_name)
TxTypeTransfer = getFlags(TxAsset_name, Transfer_name)
TxTypeCirculate = getFlags(TxAsset_name, Circulate_name)
TxTypeBind = getFlags(TxAsset_name, Bind_name)
TxTypeRevokeAsset = getFlags(TxAsset_name, RevokeAsset_name)
TxTypeCreateAccount = getFlags(TxAccount_name, CreateAccount_name)
TxTypeRevokeAccount = getFlags(TxAccount_name, RevokeAccount_name)

# Asset types
AssetFractional = "Fractional"
AssetDiscrete = "Discrete"
AssetBinary = "Binary"

# Value types
VTypeNum = 0
VTypeBool = 1
VTypeAccount = 2
VTypeAsset = 3
VTypeContract =4
VTypeText = 5
VTypeSig = 6
VTypeVoid = 7
VTypeDateTime = 8
VTypeTimeDelta = 9
VTypeEnum = 10
VTypeUndefined = 100

VTypeNumDecimal = 0
VTypeNumRational = 1

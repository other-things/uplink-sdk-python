from uplink.cryptography import derive_account_address

import reference


def test_address_derive():
    assert derive_account_address(reference.vkey) == reference.testAddr

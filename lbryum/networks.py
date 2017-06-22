"""
Main network and testnet3 definitions
"""

# these values follow the parameters in lbrycrd/src/chainparams.cpp

blockchain_params = {
    'lbrycrd_main': {
        'pubkey_address': 0,
        'script_address': 5,
        'pubkey_address_prefix': 85,
        'script_address_prefix': 122,
        'genesis_hash': '9c89283ba0f3227f6c03b70216b9f665f0118d5e0fa729cedf4fb34d6a34f463',
        'max_target': 0x0000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        'genesis_bits': 0x1f00ffff,
        'target_timespan': 150
    },
    'lbrycrd_test': {
        'pubkey_address': 0,
        'script_address': 5,
        'pubkey_address_prefix': 111,
        'script_address_prefix': 196,
        'genesis_hash': '9c89283ba0f3227f6c03b70216b9f665f0118d5e0fa729cedf4fb34d6a34f463',
        'max_target': 0x0000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        'genesis_bits': 0x1f00ffff,
        'target_timespan': 150
    },
    'lbrycrd_regtest': {
        'pubkey_address': 0,
        'script_address': 5,
        'pubkey_address_prefix': 111,
        'script_address_prefix': 196,
        'genesis_hash': '6e3fcf1299d4ec5d79c3a4c91d624a4acf9e2e173d95a1a0504f677669687556',
        'max_target': 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        'genesis_bits': 0x207fffff,
        'target_timespan': 1
    }
}

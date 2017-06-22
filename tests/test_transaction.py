import unittest

from lib import transaction
from lib.lbrycrd import TYPE_ADDRESS

unsigned_blob = '01000000012a5c9a94fcde98f5581cd00162c60a13936ceb75389ea65bf38633b424eb4031000000005701ff4c53ff0488b21e03ef2afea18000000089689bff23e1e7fb2f161daa37270a97a3d8c2e537584b2d304ecb47b86d21fc021b010d3bd425f8cf2e04824bfdf1f1f5ff1d51fadd9a41f9e3fb8dd3403b1bfe00000000ffffffff0140420f00000000001976a914230ac37834073a42146f11ef8414ae929feaafc388ac00000000'
signed_blob = '01000000012a5c9a94fcde98f5581cd00162c60a13936ceb75389ea65bf38633b424eb4031000000006c493046022100a82bbc57a0136751e5433f41cf000b3f1a99c6744775e76ec764fb78c54ee100022100f9e80b7de89de861dc6fb0c1429d5da72c2b6b2ee2406bc9bfb1beedd729d985012102e61d176da16edd1d258a200ad9759ef63adf8e14cd97f53227bae35cdb84d2f6ffffffff0140420f00000000001976a914230ac37834073a42146f11ef8414ae929feaafc388ac00000000'


class TestBCDataStream(unittest.TestCase):
    def test_compact_size(self):
        s = transaction.BCDataStream()
        values = [0, 1, 252, 253, 2 ** 16 - 1, 2 ** 16, 2 ** 32 - 1, 2 ** 32, 2 ** 64 - 1]
        for v in values:
            s.write_compact_size(v)

        with self.assertRaises(transaction.SerializationError):
            s.write_compact_size(-1)

        self.assertEquals(s.input.encode('hex'),
                          '0001fcfdfd00fdfffffe00000100feffffffffff0000000001000000ffffffffffffffffff')
        for v in values:
            self.assertEquals(s.read_compact_size(), v)

        with self.assertRaises(IndexError):
            s.read_compact_size()

    def test_string(self):
        s = transaction.BCDataStream()
        with self.assertRaises(transaction.SerializationError):
            s.read_string()

        msgs = ['Hello', ' ', 'World', '', '!']
        for msg in msgs:
            s.write_string(msg)
        for msg in msgs:
            self.assertEquals(s.read_string(), msg)

        with self.assertRaises(transaction.SerializationError):
            s.read_string()

    def test_bytes(self):
        s = transaction.BCDataStream()
        s.write('foobar')
        self.assertEquals(s.read_bytes(3), 'foo')
        self.assertEquals(s.read_bytes(2), 'ba')
        self.assertEquals(s.read_bytes(4), 'r')
        self.assertEquals(s.read_bytes(1), '')


class TestTransaction(unittest.TestCase):
    def test_tx_unsigned(self):
        expected = {
            'inputs': [{
                'address': 'bFnNVhPUNRWiA6Y2hbd1KBAMgQBrFsc5u3',
                'is_coinbase': False,
                'num_sig': 1,
                'prevout_hash': '3140eb24b43386f35ba69e3875eb6c93130ac66201d01c58f598defc949a5c2a',
                'prevout_n': 0,
                'pubkeys': ['02e61d176da16edd1d258a200ad9759ef63adf8e14cd97f53227bae35cdb84d2f6'],
                'scriptSig': '01ff4c53ff0488b21e03ef2afea18000000089689bff23e1e7fb2f161daa37270a97a3d8c2e537584b2d304ecb47b86d21fc021b010d3bd425f8cf2e04824bfdf1f1f5ff1d51fadd9a41f9e3fb8dd3403b1bfe00000000',
                'sequence': 4294967295,
                'signatures': [None],
                'x_pubkeys': [
                    'ff0488b21e03ef2afea18000000089689bff23e1e7fb2f161daa37270a97a3d8c2e537584b2d304ecb47b86d21fc021b010d3bd425f8cf2e04824bfdf1f1f5ff1d51fadd9a41f9e3fb8dd3403b1bfe00000000']}],
            'lockTime': 0,
            'outputs': [{
                'address': 'bFvZEougL4h3LnvAMr8kS1miCLsiJCpLpB',
                'prevout_n': 0,
                'scriptPubKey': '76a914230ac37834073a42146f11ef8414ae929feaafc388ac',
                'type': TYPE_ADDRESS,
                'value': 1000000}],
            'version': 1
        }
        tx = transaction.Transaction(unsigned_blob)
        self.assertEquals(tx.deserialize(), expected)
        self.assertEquals(tx.deserialize(), None)

        self.assertEquals(tx.as_dict(), {'hex': unsigned_blob, 'complete': False})
        self.assertEquals(tx.get_outputs(), [('bFvZEougL4h3LnvAMr8kS1miCLsiJCpLpB', 1000000)])
        self.assertEquals(tx.get_output_addresses(), ['bFvZEougL4h3LnvAMr8kS1miCLsiJCpLpB'])

        self.assertTrue(tx.has_address('bFvZEougL4h3LnvAMr8kS1miCLsiJCpLpB'))
        self.assertTrue(tx.has_address('bFnNVhPUNRWiA6Y2hbd1KBAMgQBrFsc5u3'))
        self.assertFalse(tx.has_address('bScaWvgzAzFXzAcVgDDARfo9RFhdrm4pVc'))

        self.assertEquals(tx.inputs_to_sign(),
                          set(x_pubkey for i in expected['inputs'] for x_pubkey in i['x_pubkeys']))
        self.assertEquals(tx.serialize(), unsigned_blob)

        tx.update_signatures(signed_blob)
        self.assertEquals(tx.raw, signed_blob)

        tx.update(unsigned_blob)
        tx.raw = None
        blob = str(tx)
        self.assertEquals(transaction.deserialize(blob), expected)

    def test_tx_signed(self):
        expected = {
            'inputs': [{
                'address': 'bFnNVhPUNRWiA6Y2hbd1KBAMgQBrFsc5u3',
                'is_coinbase': False,
                'num_sig': 1,
                'prevout_hash': '3140eb24b43386f35ba69e3875eb6c93130ac66201d01c58f598defc949a5c2a',
                'prevout_n': 0,
                'pubkeys': ['02e61d176da16edd1d258a200ad9759ef63adf8e14cd97f53227bae35cdb84d2f6'],
                'scriptSig': '493046022100a82bbc57a0136751e5433f41cf000b3f1a99c6744775e76ec764fb78c54ee100022100f9e80b7de89de861dc6fb0c1429d5da72c2b6b2ee2406bc9bfb1beedd729d985012102e61d176da16edd1d258a200ad9759ef63adf8e14cd97f53227bae35cdb84d2f6',
                'sequence': 4294967295,
                'signatures': [
                    '3046022100a82bbc57a0136751e5433f41cf000b3f1a99c6744775e76ec764fb78c54ee100022100f9e80b7de89de861dc6fb0c1429d5da72c2b6b2ee2406bc9bfb1beedd729d985'],
                'x_pubkeys': [
                    '02e61d176da16edd1d258a200ad9759ef63adf8e14cd97f53227bae35cdb84d2f6']}],
            'lockTime': 0,
            'outputs': [{
                'address': 'bFvZEougL4h3LnvAMr8kS1miCLsiJCpLpB',
                'prevout_n': 0,
                'scriptPubKey': '76a914230ac37834073a42146f11ef8414ae929feaafc388ac',
                'type': TYPE_ADDRESS,
                'value': 1000000}],
            'version': 1
        }
        tx = transaction.Transaction(signed_blob)
        self.assertEquals(tx.deserialize(), expected)
        self.assertEquals(tx.deserialize(), None)
        self.assertEquals(tx.as_dict(), {'hex': signed_blob, 'complete': True})

        self.assertEquals(tx.inputs_to_sign(), set())
        self.assertEquals(tx.serialize(), signed_blob)

        tx.update_signatures(signed_blob)

    def test_errors(self):
        with self.assertRaises(TypeError):
            transaction.Transaction.pay_script(output_type=None, addr='')

        with self.assertRaises(BaseException):
            transaction.parse_xpub('')

    def test_parse_xpub(self):
        res = transaction.parse_xpub('fd007d260305ef27224bbcf6cf5238d2b3638b5a78d5')
        self.assertEquals(res, (None, 'bQ8zhKJViSigoeyJYYLDsTLsuaBraUv74z'))


class NetworkMock(object):
    def __init__(self, unspent):
        self.unspent = unspent

    def synchronous_get(self, arg):
        return self.unspent

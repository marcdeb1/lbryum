import unittest

from lbryum import mnemonic


class Test_NewMnemonic(unittest.TestCase):
    def test_prepare_seed(self):
        seed = 'foo BAR Baz'
        self.assertEquals(mnemonic.prepare_seed(seed), 'foo bar baz')

    def test_to_seed(self):
        seed = mnemonic.Mnemonic.mnemonic_to_seed(mnemonic='foobar', passphrase='none')
        self.assertEquals(seed.encode('hex'),
                          'd4ed91101deb98cdaf516814360cc167419ce4e70da9920d83da4a2ae1cdf6d9198d45a25f4051f6e75435ec7c3e2587ab540be3c4da3f1b3d37830e2612a025')

    def test_random_seeds(self):
        iters = 10
        m = mnemonic.Mnemonic(lang='en')
        for _ in range(iters):
            seed = m.make_seed()
            self.assertTrue(m.check_seed(seed, custom_entropy=1))
            i = m.mnemonic_decode(seed)
            self.assertEquals(m.mnemonic_encode(i), seed)

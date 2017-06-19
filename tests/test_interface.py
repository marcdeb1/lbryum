import unittest

from lib import interface


class TestInterface(unittest.TestCase):
    def test_match_host_name(self):
        self.assertTrue(interface._match_hostname('asd.fgh.com', 'asd.fgh.com'))
        self.assertFalse(interface._match_hostname('asd.fgh.com', 'asd.zxc.com'))
        self.assertTrue(interface._match_hostname('asd.fgh.com', '*.fgh.com'))
        self.assertFalse(interface._match_hostname('asd.fgh.com', '*fgh.com'))
        self.assertFalse(interface._match_hostname('asd.fgh.com', '*.zxc.com'))

import re

import dns
from lbryum import lbrycrd
from lbryum.util import StoreDict


class Contacts(StoreDict):
    def __init__(self, config):
        StoreDict.__init__(self, config, 'contacts')

    def resolve(self, k):
        if lbrycrd.is_address(k):
            return {
                'address': k,
                'type': 'address'
            }
        if k in self.keys():
            _type, addr = self[k]
            if _type == 'address':
                return {
                    'address': addr,
                    'type': 'contact'
                }
        out = self.resolve_openalias(k)
        if out:
            address, name, validated = out
            return {
                'address': address,
                'name': name,
                'type': 'openalias',
                'validated': validated
            }
        raise Exception("Invalid Bitcoin address or alias", k)

    def resolve_openalias(self, url):
        # support email-style addresses, per the OA standard
        url = url.replace('@', '.')
        records, validated = dns.query(url, dns.rdatatype.TXT)
        prefix = 'btc'
        for record in records:
            string = record.strings[0]
            if string.startswith('oa1:' + prefix):
                address = self.find_regex(string, r'recipient_address=([A-Za-z0-9]+)')
                name = self.find_regex(string, r'recipient_name=([^;]+)')
                if not name:
                    name = address
                if not address:
                    continue
                return address, name, validated

    def find_regex(self, haystack, needle):
        regex = re.compile(needle)
        try:
            return regex.search(haystack).groups()[0]
        except AttributeError:
            return None
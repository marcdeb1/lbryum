#!/usr/bin/env python2

# python setup.py sdist --format=zip,gztar

from setuptools import setup
import os
import sys
import platform
import imp

version = imp.load_source('version', 'lib/version.py')

if sys.version_info[:3] < (2, 7, 0):
    sys.exit("Error: lbryum requires Python version >= 2.7.0...")

data_files = []

requires = [
    'slowaes>=0.1a1',
    'ecdsa==0.13',
    'pbkdf2',
    'requests',
    'qrcode',
    'protobuf==3.2.0',
    'dnspython',
    'jsonrpclib',
    'six>=1.9.0',
    'appdirs==1.4.3',
    'lbryschema==0.0.7'
]


if False and platform.system() in ['Linux', 'FreeBSD', 'DragonFly']:
    usr_share = os.path.join(sys.prefix, "share")
    if not os.access(usr_share, os.W_OK):
        if 'XDG_DATA_HOME' in os.environ.keys():
            usr_share = os.environ['$XDG_DATA_HOME']
        else:
            usr_share = os.path.expanduser('~/.local/share')

setup(
    name="lbryum",
    version=version.LBRYUM_VERSION,
    install_requires=requires,
    packages=[
        'lbryum',
    ],
    package_dir={
        'lbryum': 'lib',
    },
    package_data={
        'lbryum': [
            'wordlist/*.txt',
            'locale/*/LC_MESSAGES/lbryum.mo',
        ]
    },
    scripts=['lbryum'],
    data_files=data_files,
    description="Lightweight LBRYcrd Wallet",
    author="LBRY Inc.",
    author_email="hello@lbry.io",
    license="GNU GPLv3",
    url="https://lbry.io",
    long_description="""Lightweight LBRYcrd Wallet"""
)

import os
import sys

# from pkg_resources import get_distribution
from setuptools import find_packages, setup

if sys.version_info[:3] < (2, 7, 0):
    sys.exit("Error: lbryum requires Python version >= 2.7.0...")

__version__ = "2.8.4"  # get_distribution('lbryum').version

data_files = []

requires = [
    'slowaes==0.1a1',
    'ecdsa==0.13',
    'pbkdf2',
    'requests',
    'jsonrpclib',
    'six>=1.9.0',
    'appdirs==1.4.3',
    'lbryschema==0.0.7'
]

console_scripts = [
    'lbryum = lbryum.main:main',
]

base_dir = os.path.abspath(os.path.dirname(__file__))

setup(
    name="lbryum",
    version=__version__,
    install_requires=requires,
    packages=find_packages(exclude=['tests']),
    package_data={'lbryum': ['wordlist/*.txt']},
    entry_points={'console_scripts': console_scripts},
    description="Lightweight LBRYcrd Wallet",
    author="LBRY Inc.",
    author_email="hello@lbry.io",
    license="GNU GPLv3",
    url="https://lbry.io",
    long_description="""Lightweight LBRYcrd Wallet""",
    zip_safe=False
)

import logging

from lbryum import version

__version__ = version.LBRYUM_VERSION

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)

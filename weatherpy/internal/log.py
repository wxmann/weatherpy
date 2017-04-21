import logging

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
logger.addHandler(ch)
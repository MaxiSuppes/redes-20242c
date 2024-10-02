import logging

LOGGER_NAME = 'Logger'


def setup_logging(increase_verbosity, decrease_verbosity):
    if increase_verbosity:
        print("Called setup_logging with increase_verbosity=True")
        logger.setLevel(logging.DEBUG)
    elif decrease_verbosity:
        print("Called setup_logging with decrease=True")
        logger.setLevel(logging.ERROR)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(LOGGER_NAME)

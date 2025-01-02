import json
import logging
import logging.config
import os


def __create_logger_instance() -> logging.Logger:
    with open(os.path.join(os.path.dirname(__file__), 'logging.json'), 'r') as file:
        config = json.load(file)
        logging.config.dictConfig(config)

    return logging.getLogger('standard')


logger = __create_logger_instance()

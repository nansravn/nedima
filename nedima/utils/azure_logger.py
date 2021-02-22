import logging
import json
from opencensus.ext.azure.log_exporter import AzureEventHandler

from nedima.utils import env_setup


def get_logger_custom_events(secrets = env_setup.load_secrets()):
    logger = logging.getLogger('log_global')
    logger.addHandler(AzureEventHandler(connection_string=secrets['azure']['appi_connection']))
    logger.setLevel(logging.INFO)
    return logger


def log_inspection_iteration(custom_events_logger, inspection_hashtag='surf', flag_print =  False, logging_dict = {}):
    properties = {'custom_dimensions' : logging_dict.copy()}
    if flag_print:
        print(properties['custom_dimensions'])
    custom_events_logger.info("inspection_"+inspection_hashtag, extra=properties)
    logging_dict.clear()
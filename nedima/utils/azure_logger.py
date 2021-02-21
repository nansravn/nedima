import logging
import json
from opencensus.ext.azure.log_exporter import AzureEventHandler

from nedima.utils import env_setup


def get_logger_custom_event():
    secrets = env_setup.load_secrets()

    logger = logging.getLogger(__name__)
    logger.addHandler(AzureEventHandler(connection_string=secrets['azure']['appi_connection']))
    logger.setLevel(logging.INFO)

    return logger
import functools
import os
from typing import Optional

from app.calculator.computation.database import CalculatorDatabase
from app.config import ProductionConfig, Config, config_by_env
from app.util.logger import logger
from app.util.process_queue_manager import ProcessQueueManager


def singleton(cls):
    """Make a class a Singleton class (only one instance)"""

    @functools.wraps(cls)
    def wrapper_singleton(*args, **kwargs):
        if not wrapper_singleton.instance:
            wrapper_singleton.instance = cls(*args, **kwargs)
        return wrapper_singleton.instance

    wrapper_singleton.instance = None
    return wrapper_singleton


@singleton
class CalculatorProcessQueueManager(ProcessQueueManager):
    """Singleton Calculator Process Queue Manager"""
    pass


class CalculatorMicroservice:
    def __init__(self, mode):
        logger.info(f"Initializing a CalculatorMicroservice by Process-{os.getpid()}")
        self.config = initialize_config(mode)
        self.calculator_db = CalculatorDatabase(self.config)
        self.calculator_qm = initialize_calculator_process_qm(self.config)


# To be called in every child process
def initialize_config(mode):
    _config: Optional[Config] = None
    logger.info(f"Initializing config based on mode ({str(mode)}) by Process-{os.getpid()}")
    if mode in ["test", None]:
        logger.info(f"Setting global variable 'config' to be {Config.__name__}")
        _config = Config()
    else:
        logger.info(f"Setting global variable 'config' to be {ProductionConfig.__name__}")
        _config = ProductionConfig()
    return _config


# To be called in only parent process
def initialize_calculator_process_qm(config: Config):
    logger.info(f"Initializing a singleton calculator process qm by Process-{os.getpid()}")
    calculator_qm = CalculatorProcessQueueManager(service='calculator', parallelism=config.CONSUMER_PARALLELISM,
                                                  max_limit=config.QUEUE_SIZE,
                                                  queue_block_timeout=config.QUEUE_BLOCK_TIMEOUT)
    return calculator_qm


def initialize_calculator_micro_service():
    global calculator_ms
    if not calculator_ms:
        flask_microservice_env = os.getenv("FLASK_MICROSERVICE_ENV")
        calculator_ms = CalculatorMicroservice(flask_microservice_env)
    return calculator_ms


# Global variable to be set based on env variable/ during start up in main process
# Initialization is protected in entry point to prevent error in spawn child process
calculator_ms: Optional[CalculatorMicroservice] = None

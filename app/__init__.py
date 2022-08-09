import functools
import os
from typing import Optional

from app.config import ProductionConfig, Config
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


# To be called in every child process
def initialize_config():
    flask_microservice_env = os.getenv("FLASK_MICROSERVICE_ENV")
    global config
    if not config:
        logger.info(f"Initializing config based on FLASK_MICROSERVICE_ENV ({str(flask_microservice_env)})"
                    f" by Process-{os.getpid()}")
        if flask_microservice_env in ["test", None]:
            logger.info(f"Setting global variable 'config' to be {Config.__name__}")
            config = Config()
        else:
            logger.info(f"Setting global variable 'config' to be {ProductionConfig.__name__}")
            config = ProductionConfig()


# To be called in only parent process
def initialize_calculator_process_qm():
    global calculator_qm
    if not calculator_qm:
        logger.info(f"Initializing a singleton calculator process qm by Process-{os.getpid()}")
        calculator_qm = CalculatorProcessQueueManager(service='calculator')


# Global variable to be set based on env variable/ during startup
config: Optional[Config] = None
calculator_qm: Optional[ProcessQueueManager] = None

# To be initialized for parent and child processes
initialize_config()

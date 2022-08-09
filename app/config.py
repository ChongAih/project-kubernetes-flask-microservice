import os


class Config:
    CONSUMER_PARALLELISM = 1
    QUEUE_SIZE = 10
    QUEUE_BLOCK_TIMEOUT = 2  # seconds
    CALCULATOR_SQLITE_DB_NAME = "calculator_dev"
    CALCULATOR_SQLITE_TABLE_NAME = "computation_dev"
    DB_PATH = os.getcwd()


class ProductionConfig(Config):
    CONSUMER_PARALLELISM = 3
    QUEUE_SIZE = 500
    QUEUE_BLOCK_TIMEOUT = 60  # seconds
    CALCULATOR_SQLITE_DB_NAME = "calculator"
    CALCULATOR_SQLITE_TABLE_NAME = "computation"
    DB_PATH = "/database"


config_by_env = {
    "test": Config,
    "prod": ProductionConfig
}

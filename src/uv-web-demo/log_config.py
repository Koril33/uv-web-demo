from .app_config import AppConfig
import logging.config
from pathlib import Path


log_config_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] - %(levelname)-8s - %(filename)-12s - <%(funcName)-15s> :: %(message)s',
        }
    },
    'handlers': {
        'console_handler': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default',
            'level': 'DEBUG',
        },
        'error_handler': {
            'class': 'concurrent_log_handler.ConcurrentTimedRotatingFileHandler',
            'filename': 'logs/error.log',
            'formatter': 'default',
            'when': 'midnight',
            'backupCount': 3,
            'encoding': 'utf-8',
            'level': 'ERROR',
        },
        'info_handler': {
            'class': 'concurrent_log_handler.ConcurrentTimedRotatingFileHandler',
            'filename': 'logs/info.log',
            'formatter': 'default',
            'when': 'midnight',
            'backupCount': 3,
            'encoding': 'utf-8',
            'level': 'INFO',
        }
    },
    'loggers': {
        f'{AppConfig.PROJECT_NAME}': {
            'handlers': ['console_handler', 'error_handler', 'info_handler'],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
}

def init_log_config():
    Path.mkdir(Path.cwd().joinpath("logs"), parents=True, exist_ok=True)
    logging.config.dictConfig(log_config_dict)

app_logger = logging.getLogger(f'{AppConfig.PROJECT_NAME}')
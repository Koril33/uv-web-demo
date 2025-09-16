import multiprocessing

from src.uv_web_demo.app_config import AppConfig

bind = f'{AppConfig.APP_HOST}:{AppConfig.APP_PORT}'
# workers = multiprocessing.cpu_count() * 2 + 1
workers = 1

class AppConfig(object):
    # 存储公共配置
    PROJECT_NAME = "uv-web-demo"

    APP_HOST = "0.0.0.0"
    APP_PORT = 8125
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    MAX_FORM_MEMORY_SIZE = 16 * 1024 * 1024


class DevelopmentConfig(AppConfig):
    # 存储开发环境中的配置
    DB_NAME = "djhx-shelf.db"

class ProductionConfig(AppConfig):
    # 存储生产环境中的配置
    DB_NAME = "djhx-shelf.db"

config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}

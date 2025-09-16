import os

from . import create_app
from .app_config import AppConfig

app_config_mode = os.getenv('CONFIG_MODE', 'development')
app = create_app(app_config_mode)
app.run(host=AppConfig.APP_HOST, port=AppConfig.APP_PORT, debug=False)
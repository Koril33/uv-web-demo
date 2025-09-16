import os
from . import create_app

app_config_mode = os.getenv("CONFIG_MODE", "development")
app = create_app(app_config_mode)
from flask import Flask
from .configs import configs
from .controllers import config_route


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(configs[config_name])
    config_route(app)
    return app


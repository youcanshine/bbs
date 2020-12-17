from flask import Flask
from fly_bbs.configs import configs
from fly_bbs.controllers import config_blueprints
from fly_bbs.install_init import init as install_init
from fly_bbs.extensions import init_extensions
from fly_bbs.custom_functions import init_func


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(configs[config_name])
    init_extensions(app)
    config_blueprints(app)
    install_init()
    init_func(app)
    return app


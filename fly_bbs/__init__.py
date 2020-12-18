from flask import Flask
from fly_bbs.configs import configs
from fly_bbs.controllers import config_blueprints
from fly_bbs.install_init import init as install_init
from fly_bbs.extensions import init_extensions
from fly_bbs.custom_functions import init_func
from fly_bbs import flask_objectid_converter


def create_app(config_name):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'PyFly123'
    app.url_map.converters['ObjectId'] = flask_objectid_converter.ObjectIdConverter
    app.config.from_object(configs[config_name])
    init_extensions(app)
    config_blueprints(app)
    init_func(app)
    with app.app_context():
        install_init()
    return app

from flask_pymongo import PyMongo
from flask_login import LoginManager
from bson import ObjectId
from .models import User

mongo = PyMongo()
login_manager = LoginManager()
login_manager.login_view = 'user_view.login'


@login_manager.user_loader
def user_load(user_id):
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    return User(user)


def init_extensions(app):
    mongo.init_app(app)
    login_manager.init_app(app)




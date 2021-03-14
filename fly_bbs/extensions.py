from flask_pymongo import PyMongo
from flask_login import LoginManager
from bson import ObjectId
from .models import User
from flask_uploads import UploadSet, configure_uploads, IMAGES, ALL
from flask_admin import Admin
from fly_bbs.admin import admin_view
from flask_mail import Mail
from jieba.analyse import ChineseAnalyzer
from .plugins import WhooshSearcher
from whoosh.fields import *


mongo = PyMongo()
login_manager = LoginManager()
login_manager.login_view = 'user_view.login'
upload_photos = UploadSet(extensions=ALL)
admin = Admin(name='PyFLY 后台管理系统')
mail = Mail()
whoosh_searcher = WhooshSearcher()


@login_manager.user_loader
def user_load(user_id):
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    return User(user)


def init_extensions(app):
    mongo.init_app(app)
    login_manager.init_app(app)
    configure_uploads(app, upload_photos)
    admin.init_app(app)
    whoosh_searcher.init_app(app)
    with app.app_context():
        admin.add_view(admin_view.OptionsModelView(mongo.db['options'], '系统设置'))
        admin.add_view(admin_view.UsersModelView(mongo.db['users'], '用户管理'))
        admin.add_view(admin_view.CatalogsModelView(mongo.db['catalogs'],
                                                    '栏目管理', category='内容管理'))
        admin.add_view(admin_view.PostsModelView(mongo.db['posts'],
                                                 '帖子管理', category='内容管理'))
        admin.add_view(admin_view.PassagewaysModelView(mongo.db['passageways'],
                                                       '温馨通道', category='推广管理'))
        admin.add_view(admin_view.FriendLinksModelView(mongo.db['friend_links'],
                                                       '友链管理', category='推广管理'))
        admin.add_view(admin_view.PagesModelView(mongo.db['pages'], '页面管理',
                                                 category='推广管理'))
        admin.add_view(admin_view.FooterLinksModelView(mongo.db['footer_links'],
                                                       '底部链接', category='推广管理'))
        admin.add_view(admin_view.AdsModelView(mongo.db['ads'], '广告管理',
                                               category='推广管理'))
        chinese_analyzer = ChineseAnalyzer()
        post_schema = Schema(
            obj_id=ID(unique=True, stored=True),
            title=TEXT(stored=True, analyzer=chinese_analyzer),
            content=TEXT(stored=True, analyzer=chinese_analyzer),
            create_at = DATETIME(stored=True),
            catalog_id=ID(stored=True),
            user_id=ID(stored=True)
        )
        whoosh_searcher.add_index('posts', post_schema)
    mail.init_app(app)

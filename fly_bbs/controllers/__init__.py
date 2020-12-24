from .user_view import user_view
from .bbs_index import bbs_index
from .spa_poc import spa_poc

bp_list = [user_view, bbs_index, spa_poc]


def config_blueprints(app):
    for bp in bp_list:
        app.register_blueprint(bp)

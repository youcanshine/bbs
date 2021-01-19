from flask import Blueprint, flash, render_template, current_app, jsonify, url_for
from flask_login import login_required, current_user
from bson import ObjectId

from ..extensions import mongo
from .. import code_msg


api_view = Blueprint('api', __name__, url_prefix='/api')


@api_view.route('/post/delete/<ObjectId:post_id>', methods=['POST'])
@login_required
def post_delete(post_id):
    print('---------typeof post_id: isinstance-----')
    print(isinstance(post_id, ObjectId))
    print('----------------------------------------')
    post = mongo.db.posts.find_one_or_404({'_id': ObjectId(post_id)})
    if post['user_id'] != current_user.user['_id'] and not current_user.user['is_admin']:
        return jsonify(code_msg.USER_UN_HAD_PERMISSION)
    mongo.db.posts.delete_one({'_id': post_id})
    mongo.db.users.update_many({}, {'$pull': {'collections': post_id}})
    return jsonify(
        code_msg.DELETE_SUCCESS.put(
            'action', url_for('index.index', catalog_id=post['catalog_id'])
        )
    )

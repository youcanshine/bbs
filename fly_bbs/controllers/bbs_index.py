from flask import Blueprint, render_template, session, jsonify, url_for
from flask_login import current_user
from bson import ObjectId
from datetime import datetime

from .. import code_msg
from ..forms import PostForm
from ..models import R, BaseResult
from ..utils import gen_verify_num, verify_num
from ..extensions import mongo


bbs_index = Blueprint("bbs_index", __name__, template_folder='templates')


@bbs_index.route('/')
def index():
    username = session.get('username')
    return render_template('base.html', username=username)


@bbs_index.route('/add', methods=['GET', 'POST'])
@bbs_index.route('/edit/<ObjectId:post_id>', methods=['GET', 'POST'])
def add(post_id=None):
    form = PostForm()
    if form.is_submitted():
        if not form.validate():
            return jsonify(BaseResult(1, str(form.errors)))
        try:
            verify_num(form.vercode.data)
        except Exception as e:
            return '<h1>{}</h1>'.format(e), 404
        user = current_user.user
        if not user.get('is_active'):
            return jsonify(code_msg.USER_UN_ACTIVE_OR_DISABLED)
        user_coin = user.get('coin', 0)
        if form.reward.data > user_coin:
            msg = '悬赏金币不能大于拥有的金币，当前账号金币为：{}'.format(user_coin)
            return jsonify(R.ok(msg=msg))
        post = {
            'title': form.title.data,
            'catalog_id': ObjectId(form.catalog_id.data),
            'is_closed': False,
            'content': form.content.data
        }
        msg = '发帖成功'
        reward = form.reward.data
        if post_id:
            post['modified_at'] = datetime.utcnow()
            mongo.db.posts.update_one({'_id': post_id}, {'$set': post})
            msg = '修改成功'
        else:
            post['created_at'] = datetime.utcnow()
            post['reward'] = reward
            post['user_id'] = user['_id']
            mongo.db.users.update_one({'_id': user['_id']},
                                      {'$inc': {'coin': -reward}})
            print('Before: %s' % post)
            mongo.db.posts.insert_one(post)
            print('After: %s' % post)
            post_id = post['_id']
        return jsonify(R.ok(msg).put('action', url_for('.index')))
    ver_code = gen_verify_num()
    post = None
    title = '发布帖子'
    if post_id:
        post = mongo.db.posts.find_one_or_404({'_id': post_id})
        title = '编辑帖子'
    return render_template('jie/add.html', page_name='jie', form=form, ver_code=ver_code['question'],
                           is_add=(post_id is None), post=post, title=title)


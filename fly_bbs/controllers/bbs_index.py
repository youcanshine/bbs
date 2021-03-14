from flask import Blueprint, render_template, session, jsonify, url_for, request, redirect
from flask_login import current_user
from bson import ObjectId
from datetime import datetime
from pymongo import DESCENDING
from .. import code_msg
from ..forms import PostForm
from ..models import R, BaseResult, Page
from ..utils import gen_verify_num, verify_num
from ..extensions import mongo, whoosh_searcher
from ..db_utils import get_page, find_one
from whoosh import qparser, sorting
from whoosh.query import *


bbs_index = Blueprint("bbs_index", __name__, template_folder='templates')


@bbs_index.route('/')
@bbs_index.route('/page/<int:pn>/size/<int:size>')
@bbs_index.route('/page/<int:pn>')
@bbs_index.route("/catalog/<ObjectId:catalog_id>")
@bbs_index.route("/catalog/<ObjectId:catalog_id>/page/<int:pn>")
@bbs_index.route("/catalog/<ObjectId:catalog_id>/page/<int:pn>/size/<int:size>")
def index(pn=1, size=10, catalog_id=None):
    sort_key = request.values.get('sort_key', '_id')
    sort_by = (sort_key, DESCENDING)
    post_type = request.values.get('type')
    filter1 = {}
    if post_type == 'not_closed':
        filter1['is_closed'] = {'$ne': True}
    if post_type == 'is_closed':
        filter1['is_closed'] = True
    if post_type == 'is_cream':
        filter1['is_cream'] = True
    if catalog_id:
        filter1['catalog_id'] = catalog_id
    page = get_page('posts', pn=pn, filter1=filter1, size=size,
                    sort_by=sort_by)
    return render_template('post_list.html', is_index=catalog_id is None, page=page,
                           sort_key=sort_key, catalog_id=catalog_id,
                           post_type=post_type)


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


@bbs_index.route('/post/<ObjectId:post_id>/')
@bbs_index.route('/post/<ObjectId:post_id>/page/<int:pn>/')
def post_detail(post_id, pn=1):
    post = mongo.db.posts.find_one_or_404({'_id': post_id})
    if post:
        post['view_count'] = post.get('view_count', 0) + 1
        mongo.db.posts.save(post)
    post['user'] = find_one('users', {'_id': post['user_id']}) or {}
    page = get_page('comments', pn=pn, size=10, filter1={'post_id': post_id},
                    sort_by=('is_adopted', -1))
    return render_template('jie/detail.html', post=post, title=['title'],
                           page_name='jie', comment_page=page, catalog_id=post['catalog_id'])


@bbs_index.route('/comment/<ObjectId:comment_id>/')
def jump_comment(comment_id):
    comment = mongo.db.comments.find_one_or_404({'_id': comment_id})
    post_id = comment['post_id']
    pn = 1
    if not comment.get('is_adopted', False):
        comment_index = mongo.db.comments.count(
            {
                'post_id': post_id, '_id': {'$lt': comment_id}
            }
        )
        pn = comment_index // 10
        if pn == 0 or comment_index % 10 != 0:
            pn += 1
    return redirect(
        url_for('bbs_index.post_detail', post_id=post_id, pn=pn) + '#item-' + str(comment_id)
    )


@bbs_index.route('/refresh/indexes')
def refresh_indexes():
    name = request.values.get('name')
    whoosh_searcher.clear(name)
    writer = whoosh_searcher.get_writer(name)
    for item in mongo.db[name].find(
            {},
            ['_id', 'title', 'content', 'create_at', 'user_id', 'catalog_id']):
        item['obj_id'] = str(item['_id'])
        item['user_id'] = str(item['user_id'])
        item['catalog_id'] = str(item['catalog_id'])
        item.pop('_id')
        writer.add_document(**item)
    writer.commit()
    return ''


@bbs_index.route('/search')
@bbs_index.route('/search/page/<int:pn>/')
def post_search(pn=1, size=10):
    keyword = request.values.get('kw')
    if keyword is None:
        return render_template(
            'search/list.html', title='搜索', message='搜索关键字不能为空！', page=None
        )
    whoosh_searcher.clear('posts')
    writer = whoosh_searcher.get_writer('posts')
    for item in mongo.db['posts'].find(
        {},
        ['_id', 'title', 'content', 'create_at', 'user_id', 'catalog_id']
    ):
        item['obj_id'] = str(item['_id'])
        item['user_id'] = str(item['user_id'])
        item['catalog_id'] = str(item['catalog_id'])
        item.pop('_id')
        writer.add_document(**item)
    writer.commit()
    with whoosh_searcher.get_searcher('posts') as searcher:
        parser = qparser.MultifieldParser(
            ['title', 'content'],
            whoosh_searcher.get_index('posts').schema
        )
        q = parser.parse(keyword)
        print('q: ', q)
        result = searcher.search_page(
            q, pagenum=pn, pagelen=size, sortedby=sorting.ScoreFacet()
        )
        result_list = [x.fields() for x in result.results]
        # import pdb
        # pdb.set_trace()
        page = Page(
            pn, size, result=result_list, has_more=result.pagecount > pn,
            page_count=result.pagecount, total=result.total)
    return render_template(
        'search/list.html', title=keyword + '搜索结果', page=page, kw=keyword
    )

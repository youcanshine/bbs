import json
from bson import ObjectId
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from ..models import User
from ..extensions import mongo
from .. import utils
from werkzeug.security import generate_password_hash
from random import randint
from ..forms import RegisterForm, LoginForm
from flask_login import login_user, logout_user, login_required, current_user
from .. import db_utils
from .. import models
from .. import forms
from .. import code_msg


user_view = Blueprint('user', __name__, url_prefix='/user', template_folder='templates')


class MyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        super().default(o)


@user_view.route('/')
def home():
    users = list(mongo.db.users.find())
    print(users)
    return json.dumps(users, cls=MyEncoder, ensure_ascii=False)


@user_view.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.is_submitted():
        if not form.validate():
            return jsonify({'status': 50001, 'msg': str(form.errors)})
        vercode = form.vercode.data
        try:
            utils.verify_num(vercode)
        except Exception as e:
            return '<h1>{}</h1>'.format(e), 404
        user = mongo.db.users.find_one({'email': form.email.data})
        if not user:
            return jsonify({'status': 50102, 'msg': '用户不存在'})
        if not User.validate_login(user['password'], form.password.data):
            return jsonify({'status': 50000, 'msg': '密码错误'})
        if not user.get('is_active'):
            return jsonify({'status': 443, 'msg': '账号未激活'})
        login_user(User(user))
        return redirect(url_for('bbs_index.index'))
    ver_code = utils.gen_verify_num()
    return render_template('user/login.html', ver_code=ver_code['question'], form=form)


@user_view.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('bbs_index.index'))


@user_view.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.is_submitted():
        if not form.validate():
            return jsonify({'status': 50001, 'msg': str(form.errors)})
        try:
            utils.verify_num(form.vercode.data)
        except Exception as e:
            return '<h1>{}</h1>'.format(e), 404
        user = mongo.db.users.find_one({'email': form.email.data})
        if user:
            return jsonify({'status': 50000, 'msg': '该邮箱已经注册'})
        user = {
            'is_active': True,
            'coin': 0,
            'email': form.email.data,
            'username': form.username.data,
            'vip': 0,
            'reply_count': 0,
            'avatar': url_for('static',
                filename='images/avatar/{}.jpg'.format(randint(0, 12))),
            'password': generate_password_hash(form.password.data),
            'created_at': datetime.utcnow()
        }
        mongo.db.users.insert_one(user)
        return redirect(url_for('.login'))
    ver_code = utils.gen_verify_num()
    return render_template(
        'user/register.html',
        ver_code=ver_code['question'],
        form=form
    )


@user_view.route('/<ObjectId:user_id>')
@login_required
def user_home(user_id):
    user = mongo.db.users.find_one_or_404({'_id': user_id})
    return render_template('user/home.html', user=user)


@user_view.route('/messsage')
@user_view.route('/message/page/<int:pn>')
@login_required
def user_message(pn=1):
    user = current_user.user
    if user.get('unread', 0) > 0:
        mongo.db.users.update({'_id': user['_id']}, {'$set': {'unread': 0}})
    message_page = db_utils.get_page(
        'messages', pn, filter1={'user_id': user['_id']}, sort_by=('_id', -1)
    )
    return render_template(
        'user/message.html', user_page='message', page_name='user', page=message_page
    )


@user_view.route('/message/remove', methods=['POST'])
@login_required
def remove_message():
    user = current_user.user
    if request.values.get('all') == 'true':
        mongo.db.messages.delete_many({'user_id': user['_id']})
    elif request.values.get('id'):
        msg_id = ObjectId(request.values.get('id'))
        mongo.db.messages.delete_one({'_id': msg_id})
    return jsonify(models.BaseResult())


@user_view.route('/set', methods=['GET', 'POST'])
@login_required
def user_set():
    if request.method == 'POST':
        include_keys = ['username', 'avatar', 'desc', 'city', 'sex']
        data = request.values
        update_data = {}
        for key in data.keys():
            if key in include_keys:
                update_data[key] = data.get(key)
        mongo.db.users.update(
            {'_id': current_user.user['_id']}, {'$set': update_data}
        )
        return jsonify('修改成功')
    return render_template(
        'user/set.html', user_page='set', page_name='user', title='基本设置'
    )


@user_view.route('/repass', methods=['POST'])
def user_repass():
    if not current_user.is_authenticated:
        redirect(url_for('user.login'))
    pwd_form = forms.ChangePassWordForm()
    if not pwd_form.validate():
        return jsonify(
            models.R.fail(
                code_msg.PARAM_ERROR.get_msg(),
                str(pwd_form.errors)
            )
        )
    nowpassword = pwd_form.nowpassword.data
    password = pwd_form.password.data
    user = current_user.user
    if not models.User.validate_login(user['password'], nowpassword):
        raise Exception(code_msg.PASSWORD_ERROR)
    mongo.db.users.update(
        {'_id': user['_id']}, {'$set': {'password': generate_password_hash(password)}}
    )
    return jsonify(models.R.ok())


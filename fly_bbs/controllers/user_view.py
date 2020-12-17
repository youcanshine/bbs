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
from flask_login import login_user, logout_user


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

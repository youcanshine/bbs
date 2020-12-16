import json
from bson import ObjectId
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from ..models import User
from ..extensions import mongo
from .. import utils

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
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = mongo.db.users.find_one({'email': email})
        vercode = request.form.get('vercode')
        try:
            utils.verify_num(vercode)
        except Exception as e:
            return '<h1>{}</h1>'.format(e), 404
        if not user:
            return jsonify({'status': 50102, 'msg': '用户不存在'})
        if not User.validate_login(user['password'], password):
            return jsonify({'status': 50000, 'msg': '密码错误'})
        session['username'] = user['username']
        # return '<h1>登录成功</h1>'
        return redirect(url_for('bbs_index.index'))
    ver_code = utils.gen_verify_num()
    return render_template('user/login.html', ver_code=ver_code['question'])


@user_view.route('/register')
def register():
    return render_template('user/register.html')

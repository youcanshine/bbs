import json
from bson import ObjectId
from datetime import datetime
from flask import Blueprint, abort, render_template, request, jsonify, redirect, url_for, session
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


def send_active_email(username, user_id, email, is_forget=False):
    code = mongo.db.active_codes.insert_one({'user_id': user_id})
    if is_forget:
        body = render_template(
            'email/user_repwd.html',
            url=url_for('user.user_pass_forget', code=code.inserted_id, _external=True)
        )
        utils.send_email(email, '重置密码', body=body)
        return
    body = render_template(
        'email/user_active.html', username=username,
        url=url_for('user.user_active', code=code.inserted_id, _external=True)
    )
    utils.send_email(email, '账号激活', body=body)


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
            'is_active': False,
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
        insert_result = mongo.db.users.insert_one(user)
        # utils.send_email(form.email.data, '你激活了',
        #                  body='你已经成功注册了账号，同时完成了发送邮件功能！')
        # mongo.db.users.update_one(
        #     {'username': form.username.data}, {'$set': {'is_active': True}}
        # )
        send_active_email(form.username.data, insert_result.inserted_id, form.email.data)
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


# @user_view.route('/repass', methods=['POST'])
# def user_repass():
#     if not current_user.is_authenticated:
#         redirect(url_for('user.login'))
#     pwd_form = forms.ChangePassWordForm()
#     if not pwd_form.validate():
#         return jsonify(
#             models.R.fail(
#                 code_msg.PARAM_ERROR.get_msg(),
#                 str(pwd_form.errors)
#             )
#         )
#     nowpassword = pwd_form.nowpassword.data
#     password = pwd_form.password.data
#     user = current_user.user
#     if not models.User.validate_login(user['password'], nowpassword):
#         raise Exception(code_msg.PASSWORD_ERROR)
#     mongo.db.users.update(
#         {'_id': user['_id']}, {'$set': {'password': generate_password_hash(password)}}
#     )
#     return jsonify(models.R.ok())


@user_view.route('/active', methods=['GET', 'POST'])
def user_active():
    if request.method == 'GET':
        code = request.values.get('code')
        if code:
            user_id = mongo.db.active_codes.find_one(
                {'_id': ObjectId(code)}
            ).get('user_id')
            if user_id:
                mongo.db.active_codes.delete_many({'user_id': ObjectId(user_id)})
                mongo.db.users.update(
                    {'_id': user_id}, {'$set': {'is_active': True}}
                )
                user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
                login_user(models.User(user))
                return render_template('user/activate.html')
        if not current_user.is_authenticated:
            abort(403)
        return render_template('user/activate.html')
    user = current_user.user
    mongo.db.active_codes.delete_many({'user_id': ObjectId(user['_id'])})
    send_active_email(user['username'], user['_id'], user['email'])
    return jsonify(code_msg.RE_ACTIVATE_MAIL_SEND.put('action', url_for('user.user_active')))


@user_view.route('/forget', methods=['POST', 'GET'])
def user_pass_forget():
    code = request.args.get('code')
    mail_form = forms.SendForgetMailForm()
    if mail_form.is_submitted():
        if not mail_form.validate():
            return jsonify(
                models.R.fail(
                    code_msg.PARAM_ERROR.get_msg(),
                    str(mail_form.errors)
                )
            )
        email = mail_form.email.data
        ver_code = mail_form.vercode.data
        utils.verify_num(ver_code)
        user = mongo.db.users.find_one({'email': email})
        if not user:
            return jsonify(code_msg.USER_NOT_EXIST)
        send_active_email(user['username'], user_id=user['_id'], email=email, is_forget=True)
        return jsonify(code_msg.RE_PWD_MAIL_SEND.put('action', url_for('user.login')))
    has_code = False
    user = None
    if code:
        active_code = mongo.db.active_codes.find_one({'_id': ObjectId(code)})
        if not active_code:
            return render_template(
                'user/forget.html', page_name='user', has_code=True, code_invalid=True
            )
        has_code = True
        user = mongo.db.users.find_one({'_id': active_code['user_id']})
    ver_code = utils.gen_verify_num()

    return render_template(
        'user/forget.html', page_name='user', ver_code=ver_code['question'],
        code=code, has_code=has_code, user=user
    )


@user_view.route('/repass', methods=['POST'])
def user_repass():
    if 'email' in request.values:
        pwd_form = forms.ForgetPasswordForm()
        if not pwd_form.validate():
            return jsonify(models.R.fail(code_msg.PARAM_ERROR.get_msg(), str(pwd_form.errors)))
        email = pwd_form.email.data
        ver_code = pwd_form.vercode.data
        code = pwd_form.code.data
        password = pwd_form.password.data
        utils.verify_num(ver_code)
        active_code = mongo.db.active_codes.find_one_or_404({'_id': ObjectId(code)})
        mongo.db.active_codes.delete_one({'_id': ObjectId(code)})
        user = mongo.db.users.update(
            {'_id': active_code['user_id'], 'email': email},
            {'$set': {'password': generate_password_hash(password)}}
        )
        if user['nModified'] == 0:
            return jsonify(code_msg.CHANGE_PWD_FAIL.put('action', url_for('user.login')))
        return jsonify(code_msg.CHANGE_PWD_SUCCESS.put('action', url_for('user.login')))
    if not current_user.is_authenticated:
        return redirect(url_for('user.login'))
    pwd_form = forms.ChangePassWordForm()
    if not pwd_form.validate():
        return jsonify(models.R.fail(code_msg.PARAM_ERROR.get_msg(), str(pwd_form.errors)))
    nowpassword = pwd_form.nowpassword.data
    password = pwd_form.password.data
    user = current_user.user
    if not models.User.validate_login(user['password'], nowpassword):
        raise Exception(">>> Password error")
    mongo.db.users.update({'_id': user['_id']}, {'$set': {'password': generate_password_hash(password)}})
    return jsonify(models.R.ok())

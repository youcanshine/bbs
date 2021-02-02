from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, InputRequired
)
from . import code_msg


class RegisterForm(FlaskForm):
    email = StringField(validators=[DataRequired('不能为空'), Email('请输入正确的邮箱格式')])
    username = StringField(validators=[DataRequired('不能为空')])
    password = PasswordField(validators=[DataRequired('不能为空'), Length(3, 26, '密码长度尾3 ~ 26个字符')])
    repeat_password = PasswordField(validators=[
        EqualTo('password', '两次输入的密码不一致')])
    vercode = StringField(validators=[InputRequired('答案写错了')])


class LoginForm(FlaskForm):
    email = StringField(validators=[DataRequired('邮箱不能为空')])
    password = PasswordField(validators=[DataRequired('密码不能为空'),
                                         Length(3, 26, '密码长度为3 ~ 26个字符')])
    vercode = StringField(validators=[InputRequired('答案写错了')])


class PostForm(FlaskForm):
    id = StringField()
    title = StringField(validators=[DataRequired('帖子标题不能为空')])
    content = StringField(validators=[DataRequired('帖子内容不能为空')])
    catalog_id = StringField(validators=[DataRequired('帖子种类不能为空')])
    reward = IntegerField(validators=[InputRequired('帖子悬赏不能为空')])
    vercode = StringField(validators=[InputRequired('验证码不能为空')])


class ChangePassWordForm(FlaskForm):
    nowpassword = StringField(
        validators=[DataRequired(code_msg.NOW_PASSWORD_EMPTY.get_msg())]
    )
    password = PasswordField(
        validators=[Length(min=6, max=6, message=code_msg.PASSWORD_LENGTH_ERROR.get_msg())]
    )
    repassword = PasswordField(
        validators=[EqualTo('password', code_msg.PASSWORD_REPEAT_ERROR.get_msg())]
    )


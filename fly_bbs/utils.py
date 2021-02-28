import random
from flask import session, current_app
from flask_mail import Message
from threading import Thread
from . import extensions


def gen_verify_num():
    a = random.randint(-20, 20)
    b = random.randint(0, 50)
    data = {
        'question': '%s + %s = ?' % (a, b),
        'answer': str(a+b)
    }
    session['ver_code'] = data['answer']
    return data


def verify_num(code):
    if code != session['ver_code']:
        raise Exception('验证码错啦! ')


def send_email(to, subject, body, is_txt=True):
    app = current_app._get_current_object()
    msg = Message(subject=app.config.get('MAIL_SUBJECT_PREFIX') + subject,
                  sender=app.config.get('MAIL_USERNAME'), recipients=[to])
    if is_txt:
        msg.body = body
    else:
        msg.html = body
    thr = Thread(target=send_mail_async, args=[app, msg])
    thr.start()
    return thr


def send_mail_async(app, msg):
    with app.app_context():
        extensions.mail.send(msg)

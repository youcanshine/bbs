from flask import Blueprint, render_template, session


bbs_index = Blueprint("bbs_index", __name__, template_folder='templates')


@bbs_index.route('/')
def index():
    username = session.get('username')
    return render_template('base.html', username=username)

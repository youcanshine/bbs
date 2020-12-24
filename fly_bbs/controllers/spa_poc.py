from flask import Blueprint, render_template, session, jsonify, url_for


spa_poc = Blueprint("spa_poc", __name__, template_folder='templates')


@spa_poc.route('/poc')
def poc():
    return render_template('spa_poc/base_poc.html')


@spa_poc.route('/poc_2')
def poc_2():
    return render_template('spa_poc/poc_2.html')

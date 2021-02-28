from flask import Blueprint, render_template, session, jsonify, url_for, request


spa_poc = Blueprint("spa_poc", __name__, template_folder='templates')


@spa_poc.route('/poc')
def poc():
    return render_template('spa_poc/base_poc.html')


@spa_poc.route('/poc_2')
def poc_2():
    return render_template('spa_poc/poc_2.html')


@spa_poc.route('/csv_upload', methods=['POST', 'GET'])
def csv_upload():
    if request.method == 'POST':
        import pdb
        pdb.set_trace()
    return render_template('spa_poc/csv_upload.html')


@spa_poc.route('/csv_check/<file_id>')
def csv_check(file_id):
    return jsonify({'status': 'success', 'payload': ''})

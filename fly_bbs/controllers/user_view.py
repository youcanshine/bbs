import json
from bson import ObjectId
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify

from ..extensions import mongo

user_view = Blueprint('user', __name__, url_prefix='/user')


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


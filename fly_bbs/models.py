from werkzeug.security import check_password_hash


class R(dict):
    @staticmethod
    def ok(msg=None, data=None):
        r = R()
        r.put('status', 0)
        r.put('msg', msg)
        r.put('data', data)
        return r

    @staticmethod
    def fail(code=404, msg=None):
        r = R()
        r.put('status', code)
        r.put('msg', msg)
        return r

    def put(self, k, v):
        self.__setitem__(k, v)
        return self

    def get_status(self):
        return self.get('status')

    def get_msg(self):
        return self.get('msg')


class BaseResult(R):
    def __init__(self, code=0, msg='', data=None):
        self.put('status', code)
        self.put('msg', msg)
        self.put('data', data)


class User:
    user = None
    is_active = False
    is_authenticated = True
    is_anonymous = False

    def __init__(self, user):
        self.user = user
        self.is_active = user['is_active']

    def get_id(self):
        return str(self.user['_id'])

    @staticmethod
    def validate_login(password_hash, password):
        return check_password_hash(password_hash, password)



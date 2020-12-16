from werkzeug.security import check_password_hash


class User:
    @staticmethod
    def validate_login(password_hash, password):
        return check_password_hash(password_hash, password)



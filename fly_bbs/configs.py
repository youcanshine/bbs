import os
from flask_uploads import ALL


class DevConfig:
    '''开发环境配置'''

    MONGO_URI = 'mongodb://localhost:27017/pyfly'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'odawara')
    WTF_CSRF_ENABLED = False
    UPLOADED_PHOTOS_ALLOW = ALL
    UPLOADED_PHOTOS_DEST = os.path.join(os.getcwd(), 'uploads')
    UPLOADED_FILES_DEST = os.path.join(os.getcwd(), 'uploads')
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 25
    MAIL_USERNAME = 'inseader@qq.com'#os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = 'gvptekdudkllhbgi'#os.environ.get('MAIL_PASSWORD')
    MAIL_SUBJECT_PREFIX = '[PyFLY]-'
    WHOOSH_PATH = os.path.join(os.getcwd(), 'whoosh_indexes')


class ProConfig(DevConfig):
    '''生产环境配置'''


configs = {
        'Dev': DevConfig,
        'Pro': ProConfig
}

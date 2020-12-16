import os


class DevConfig:
    '''开发环境配置'''

    MONGO_URI = 'mongodb://localhost:27017/pyfly'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'odawara')


class ProConfig(DevConfig):
    '''生产环境配置'''


configs = {
        'Dev': DevConfig,
        'Pro': ProConfig
}

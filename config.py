import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config():
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    FAS_OPENID_ENDPOINT = 'https://id.centos.org/idp/openid/'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    
class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    SESSION_COOKIE_HTTPONLY = False


class TestingConfig(Config):
    TESTING = True
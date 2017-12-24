#!/usr/bin/env python
#-*-coding:utf-8-*-
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    FLASKY_MAIL_SUBJECT_PREFIX= '[Flasky]'
    FLASKY_MAIL_SENDER = '1073512353@qq.com '
    FLASKY_ADMIN = '1073512353@qq.com'
    FLASKY_POSTS_PER_PAGE=15
    FLASKY_COMMENTS_PER_PAGE=15
    FLASKY_FOLLOWERS_PER_PAGE=15
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')

    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT =25
    MAIL_USE_TLS = True
    MAIL_USERNAME ='1073512353'
    MAIL_PASSWORD = 'bdktjejtvfgxbcab'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')

config= { 'development': DevelopmentConfig ,'testing': TestingConfig,\
          'production': ProductionConfig,'default': DevelopmentConfig }

if __name__ == "__main__":
    pass
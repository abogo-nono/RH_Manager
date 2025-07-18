import os

class Config:
    SECRET_KEY = 'flask_key'
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://kalash_mdb:@localhost/rh_manager_db'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///rh_manager.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'gptc33074@gmail.com'
    MAIL_PASSWORD = 'Mail_App_PassWord'
    MAIL_DEFAULT_SENDER = 'gptc33074@gmail.com'


import os

class Config:
    SECRET_KEY = 'SuperSecret'
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:@localhost/marketdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
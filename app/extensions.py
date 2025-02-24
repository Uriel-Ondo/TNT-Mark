from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api
from flask_socketio import SocketIO

db = SQLAlchemy()
api = Api()
socketio = SocketIO()
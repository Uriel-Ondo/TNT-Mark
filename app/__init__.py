from flask import Flask
from config import Config
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, JWTManager
from app.extensions import db, api, socketio
from flask_migrate import Migrate
import os


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    
    # Configuration pour les fichiers uploadés
    app.config['UPLOAD_FOLDER'] = 'uploads'  # Dossier pour stocker les images
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}  # Extensions autorisées

    # Créez le dossier 'uploads' s'il n'existe pas
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])


    # Initialisation de db et api avec l'application
    db.init_app(app)
    api.init_app(app)
    socketio.init_app(app)

    # Initialisation de Flask-Migrate
    migrate = Migrate(app, db)
    
    # Initialisation de JWT
    jwt = JWTManager(app)

    # Importez et enregistrez les namespaces
    from app.routes import user_ns, product_ns, auction_ns, auth_ns, tnt_ns
    api.add_namespace(user_ns)
    api.add_namespace(product_ns)
    api.add_namespace(auction_ns)
    api.add_namespace(auth_ns)
    api.add_namespace(tnt_ns)

    return app
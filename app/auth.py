from flask import jsonify
from flask_jwt_extended import create_access_token
from app.models import User

def login(email, password):
    user = User.query.filter_by(email=email).first()  # Recherchez l'utilisateur par email
    if user and user.password_hash == password:  # Remplacez par une vérification de hachage en production
        access_token = create_access_token(identity=user.username)  # Utilisez le username comme identité
        return jsonify(access_token=access_token)
    return jsonify({"msg": "Bad email or password"}), 401
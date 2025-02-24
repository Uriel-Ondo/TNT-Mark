from app.extensions import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(50))  # 'admin', 'client', 'commerçant'

    def __repr__(self):
        return '<User {}>'.format(self.username)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller = db.relationship('User', backref=db.backref('products', lazy=True))
    image_path = db.Column(db.String(255))  # Chemin local de l'image

    def __repr__(self):
        return f'<Product {self.name}>'

class Auction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    current_bid = db.Column(db.Float, nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product = db.relationship('Product', backref=db.backref('auctions', lazy=True))
    buyer = db.relationship('User', backref=db.backref('bids', lazy=True))

    def get_time_left(self):
        """Retourne le temps restant de l'enchère en secondes"""
        return (self.end_time - datetime.utcnow()).total_seconds()
    

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    auction_id = db.Column(db.Integer, db.ForeignKey('auction.id'))
    message = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('messages', lazy=True))
    auction = db.relationship('Auction', backref=db.backref('chat_messages', lazy=True))
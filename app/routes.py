from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from flask import request
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import User, Product, Auction, ChatMessage
from datetime import datetime
from flask_socketio import emit
from app import socketio

# Namespaces
user_ns = Namespace('user', description='User operations')
product_ns = Namespace('product', description='Product operations')
auction_ns = Namespace('auction', description='Auction operations')
auth_ns = Namespace('auth', description='Authentication operations')
tnt_ns = Namespace('tnt', description='TNT integration')

# Modèles
user_model = user_ns.model('User', {
    'id': fields.Integer(readOnly=True, description='The user unique identifier'),
    'username': fields.String(required=True, description='The user username'),
    'email': fields.String(required=True, description='The user email'),
    'role': fields.String(required=True, description='The user role')
})

signup_model = user_ns.model('SignUp', {
    'username': fields.String(required=True, description='The user username'),
    'email': fields.String(required=True, description='The user email'),
    'password': fields.String(required=True, description='The user password'),
    'role': fields.String(required=True, description='The user role (client, commerçant, admin)')
})

product_model = product_ns.model('Product', {
    'id': fields.Integer(readOnly=True, description='The product unique identifier'),
    'name': fields.String(required=True, description='The product name'),
    'description': fields.String(required=True, description='The product description'),
    'price': fields.Float(required=True, description='The product price'),
    'quantity': fields.Integer(required=True, description='The product quantity'),
    'seller_id': fields.Integer(required=True, description='The seller ID'),
    'image_path': fields.String(description='The local path of the product image')
})

auction_model = auction_ns.model('Auction', {
    'id': fields.Integer(readOnly=True, description='The auction unique identifier'),
    'product_id': fields.Integer(required=True, description='The product ID'),
    'start_time': fields.DateTime(required=True, description='The auction start time'),
    'end_time': fields.DateTime(required=True, description='The auction end time'),
    'current_bid': fields.Float(required=True, description='The current bid amount'),
    'buyer_id': fields.Integer(description='The buyer ID')
})

login_model = auth_ns.model('Login', {
    'email': fields.String(required=True, description='The user email'),
    'password': fields.String(required=True, description='The user password')
})

# Routes pour les utilisateurs
@user_ns.route('/')
class UserList(Resource):
    @user_ns.marshal_list_with(user_model)
    def get(self):
        '''List all users'''
        return User.query.all()

@user_ns.route('/<int:id>')
@user_ns.response(404, 'User not found')
@user_ns.param('id', 'The user identifier')
class UserDetail(Resource):
    @user_ns.marshal_with(user_model)
    def get(self, id):
        '''Fetch a user given its identifier'''
        return User.query.get_or_404(id)

    @user_ns.expect(signup_model)
    @jwt_required()
    def put(self, id):
        '''Update a user given its identifier'''
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        target_user = User.query.get_or_404(id)

        if user.id != target_user.id and user.role != 'admin':
            return {'message': 'You are not authorized to update this user'}, 403

        data = request.get_json()
        target_user.username = data.get('username', target_user.username)
        target_user.email = data.get('email', target_user.email)
        target_user.password_hash = generate_password_hash(data.get('password', target_user.password_hash))
        target_user.role = data.get('role', target_user.role)

        db.session.commit()
        return {'message': 'User updated successfully'}, 200

    @jwt_required()
    def delete(self, id):
        '''Delete a user given its identifier'''
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        target_user = User.query.get_or_404(id)

        if user.id != target_user.id and user.role != 'admin':
            return {'message': 'You are not authorized to delete this user'}, 403

        db.session.delete(target_user)
        db.session.commit()
        return {'message': 'User deleted successfully'}, 200

@user_ns.route('/signup')
class SignUp(Resource):
    @user_ns.expect(signup_model)
    def post(self):
        '''Register a new user'''
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')

        if User.query.filter_by(username=username).first():
            return {'message': 'Username already exists'}, 400

        if User.query.filter_by(email=email).first():
            return {'message': 'Email already exists'}, 400

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        return {'message': 'User created successfully'}, 201

# Route pour la connexion
@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    def post(self):
        '''Login and get an access token'''
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            access_token = create_access_token(identity=user.username)
            return {'access_token': access_token}, 200
        return {'message': 'Bad email or password'}, 401

# Gestionnaires WebSocket
@socketio.on('connect')
def handle_connect():
    emit('auction_update', {'message': 'Welcome to the auction!'})

@socketio.on('bid_update')
def handle_bid_update(data):
    auction_id = data['auction_id']
    bid_value = data['bid_value']
    auction = Auction.query.get(auction_id)
    
    # Mettre à jour l'enchère en temps réel
    auction.current_bid = bid_value
    db.session.commit()

    # Diffuser la mise à jour à tous les clients
    emit('auction_update', {'auction_id': auction.id, 'current_bid': bid_value}, broadcast=True)

@socketio.on('chat_message')
def handle_chat_message(data):
    user = get_jwt_identity()
    message = data['message']
    auction_id = data['auction_id']
    
    # Sauvegarder le message dans la base de données
    chat_message = ChatMessage(user_id=user.id, auction_id=auction_id, message=message)
    db.session.add(chat_message)
    db.session.commit()

    # Diffuser le message à tous les clients
    emit('new_chat_message', {'user': user.username, 'message': message, 'auction_id': auction_id}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# Routes pour les produits
@product_ns.route('/')
class ProductList(Resource):
    @product_ns.marshal_list_with(product_model)
    def get(self):
        '''List all products'''
        return Product.query.all()

    @product_ns.expect(product_model)
    @jwt_required()
    def post(self):
        '''Create a new product'''
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()

        if user.role != 'commerçant':
            return {'message': 'Only sellers can add products'}, 403

        data = request.get_json()
        new_product = Product(
            name=data['name'],
            description=data['description'],
            price=data['price'],
            quantity=data['quantity'],
            seller_id=user.id,
            image_path=data.get('image_path')
        )
        db.session.add(new_product)
        db.session.commit()

        return {'message': 'Product created successfully', 'product_id': new_product.id}, 201

@product_ns.route('/<int:id>')
@product_ns.response(404, 'Product not found')
@product_ns.param('id', 'The product identifier')
class ProductDetail(Resource):
    @product_ns.marshal_with(product_model)
    def get(self, id):
        '''Fetch a product given its identifier'''
        return Product.query.get_or_404(id)

    @product_ns.expect(product_model)
    @jwt_required()
    def put(self, id):
        '''Update a product given its identifier'''
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        product = Product.query.get_or_404(id)

        if user.id != product.seller_id:
            return {'message': 'You are not authorized to update this product'}, 403

        data = request.get_json()
        product.name = data.get('name', product.name)
        product.description = data.get('description', product.description)
        product.price = data.get('price', product.price)
        product.quantity = data.get('quantity', product.quantity)
        product.image_path = data.get('image_path', product.image_path)

        db.session.commit()
        return {'message': 'Product updated successfully'}, 200

    @jwt_required()
    def delete(self, id):
        '''Delete a product given its identifier'''
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        product = Product.query.get_or_404(id)

        if user.id != product.seller_id:
            return {'message': 'You are not authorized to delete this product'}, 403

        # Supprimez l'image associée si elle existe
        if product.image_path and os.path.exists(product.image_path):
            os.remove(product.image_path)

        db.session.delete(product)
        db.session.commit()
        return {'message': 'Product deleted successfully'}, 200

# Routes pour les enchères
@auction_ns.route('/')
class AuctionList(Resource):
    @auction_ns.marshal_list_with(auction_model)
    def get(self):
        '''List all auctions'''
        return Auction.query.all()

    @auction_ns.expect(auction_model)
    @jwt_required()
    def post(self):
        '''Create a new auction'''
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()

        if user.role != 'commerçant':
            return {'message': 'Only sellers can create auctions'}, 403

        data = request.get_json()
        new_auction = Auction(
            product_id=data['product_id'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            current_bid=data['current_bid'],
            buyer_id=None
        )
        db.session.add(new_auction)
        db.session.commit()

        return {'message': 'Auction created successfully'}, 201

@auction_ns.route('/<int:id>')
@auction_ns.response(404, 'Auction not found')
@auction_ns.param('id', 'The auction identifier')
class AuctionDetail(Resource):
    @auction_ns.marshal_with(auction_model)
    def get(self, id):
        '''Fetch an auction given its identifier'''
        return Auction.query.get_or_404(id)

    @auction_ns.expect(auction_model)
    @jwt_required()
    def put(self, id):
        '''Update an auction given its identifier'''
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        auction = Auction.query.get_or_404(id)
        product = Product.query.get_or_404(auction.product_id)

        if user.id != product.seller_id:
            return {'message': 'You are not authorized to update this auction'}, 403

        data = request.get_json()
        auction.start_time = data.get('start_time', auction.start_time)
        auction.end_time = data.get('end_time', auction.end_time)
        auction.current_bid = data.get('current_bid', auction.current_bid)

        db.session.commit()
        return {'message': 'Auction updated successfully'}, 200

    @jwt_required()
    def delete(self, id):
        '''Delete an auction given its identifier'''
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        auction = Auction.query.get_or_404(id)
        product = Product.query.get_or_404(auction.product_id)

        if user.id != product.seller_id:
            return {'message': 'You are not authorized to delete this auction'}, 403

        db.session.delete(auction)
        db.session.commit()
        return {'message': 'Auction deleted successfully'}, 200

# Route pour la simulation TNT
@tnt_ns.route('/market')
class TNTMarket(Resource):
    def get(self):
        '''Simulate TNT market data'''
        market_data = {
            'products': [
                {'name': 'Tomatoes', 'price': 2.5, 'quantity': 100},
                {'name': 'Potatoes', 'price': 1.8, 'quantity': 200},
                {'name': 'Carrots', 'price': 1.2, 'quantity': 150}
            ],
            'message': 'This is a simulated TNT market data'
        }
        return market_data, 200
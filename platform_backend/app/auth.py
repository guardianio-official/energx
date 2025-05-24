from flask import Blueprint, request, jsonify
from .models import User
from . import db, bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    organization_name = data.get('organization_name')
    roles = data.get('roles', 'user') # Default role

    if not username or not email or not password:
        return jsonify({"msg": "Missing username, email, or password"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username already exists"}), 409 # 409 Conflict

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already exists"}), 409

    try:
        new_user = User(
            username=username,
            email=email,
            password=password, # Password will be hashed in the User model's __init__ or set_password
            organization_name=organization_name,
            roles=roles
        )
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to create user", "error": str(e)}), 500


    # Optionally, return a JWT token upon successful registration
    access_token = create_access_token(identity={'username': new_user.username, 'roles': new_user.roles.split(',')})
    return jsonify(access_token=access_token, user=new_user.to_dict()), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON in request"}), 400

    identifier = data.get('identifier') # Can be username or email
    password = data.get('password')

    if not identifier or not password:
        return jsonify({"msg": "Missing username/email or password"}), 400

    user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity={'username': user.username, 'roles': user.roles.split(',') if user.roles else []})
        return jsonify(access_token=access_token, user=user.to_dict()), 200
    else:
        return jsonify({"msg": "Bad username/email or password"}), 401

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True) # Requires a valid refresh token
def refresh():
    current_user_identity = get_jwt_identity() # This will be the identity from the refresh token
    new_access_token = create_access_token(identity=current_user_identity, fresh=False)
    return jsonify(access_token=new_access_token), 200

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import User

bp = Blueprint('user', __name__)

@bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user_identity = get_jwt_identity()
    # The identity is a dictionary like {'username': 'testuser', 'roles': ['user']}
    username = current_user_identity.get('username')

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"msg": "User not found"}), 404

    return jsonify(user=user.to_dict()), 200

# Example of a route requiring specific roles (more advanced)
@bp.route('/admin/data', methods=['GET'])
@jwt_required()
def admin_data():
    current_user_identity = get_jwt_identity()
    roles = current_user_identity.get('roles', [])

    if 'admin' not in roles:
        return jsonify({"msg": "Admins only!"}), 403 # Forbidden

    # Proceed with admin-specific logic
    return jsonify(data="This is sensitive admin data.", user_roles=roles), 200

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import User, Trade, Order, HydrogenProduct, db
import logging

bp = Blueprint('trades', __name__)
logger = logging.getLogger(__name__)

def get_current_user():
    """Helper function to get the current authenticated user."""
    user_identity = get_jwt_identity()
    username = user_identity.get('username')
    return User.query.filter_by(username=username).first()

# Trade History Endpoints

@bp.route('', methods=['GET'])
@jwt_required()
def list_user_trades():
    """
    Get a list of trades where the authenticated user is either the buyer or the seller.
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({"msg": "User not found or token invalid"}), 401

    # Query for trades where the user is either the buyer or the seller
    trades = Trade.query.filter(
        (Trade.buyer_id == current_user.id) | (Trade.seller_id == current_user.id)
    ).order_by(Trade.trade_timestamp.desc()).all()

    return jsonify([trade.to_dict() for trade in trades]), 200

@bp.route('/<int:trade_id>', methods=['GET'])
@jwt_required()
def get_trade_details(trade_id):
    """
    Get details of a specific trade, if the user is involved or is an admin.
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({"msg": "User not found or token invalid"}), 401

    trade = db.session.get(Trade, trade_id) # Use db.session.get for primary key lookup

    if not trade:
        return jsonify({"msg": "Trade not found"}), 404

    user_identity = get_jwt_identity()
    is_admin = 'admin' in user_identity.get('roles', [])

    if trade.buyer_id == current_user.id or trade.seller_id == current_user.id or is_admin:
        return jsonify(trade.to_dict()), 200
    else:
        return jsonify({"msg": "Not authorized to view this trade"}), 403


@bp.route('/product/<int:product_id>', methods=['GET'])
@jwt_required() # Or make public/admin only depending on requirements
def list_trades_for_product(product_id):
    """
    Get a list of all trades for a specific hydrogen product.
    Accessible by users involved in those trades or admins.
    """
    current_user = get_current_user()
    product = db.session.get(HydrogenProduct, product_id)
    if not product:
        return jsonify({"msg": f"Product with id {product_id} not found."}), 404

    # For general users, this might be too much information unless they are the product owner.
    # For POC, let's restrict to admin or product owner.
    user_identity = get_jwt_identity()
    is_admin = 'admin' in user_identity.get('roles', [])

    if product.seller_id != current_user.id and not is_admin:
         return jsonify({"msg": "Not authorized to view trades for this product unless you are the product owner or an admin."}), 403

    trades = Trade.query.filter_by(hydrogen_product_id=product_id).order_by(Trade.trade_timestamp.desc()).all()
    return jsonify([trade.to_dict() for trade in trades]), 200


@bp.route('/orderbook/<int:product_id>', methods=['GET'])
# @jwt_required() # Could be public or protected
def get_product_order_book(product_id):
    """
    Gets the current order book (pending buy and sell orders) for a specific product.
    This uses the helper function from the matching engine module.
    """
    from .matching_engine import get_order_book_for_product # Local import to avoid circular deps at module level

    product = db.session.get(HydrogenProduct, product_id)
    if not product:
        return jsonify({"msg": f"Product with id {product_id} not found."}), 404

    order_book = get_order_book_for_product(product_id)
    return jsonify(order_book), 200

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import User, Order, HydrogenProduct, db, Trade # Added Trade
from decimal import Decimal, InvalidOperation
from datetime import datetime
from .matching_engine import attempt_match_order # Import the matching engine
import logging

bp = Blueprint('orders', __name__)
logger = logging.getLogger(__name__)

def get_current_user():
    """Helper function to get the current authenticated user."""
    user_identity = get_jwt_identity()
    username = user_identity.get('username')
    return User.query.filter_by(username=username).first()

# Order (Bidding/Offering) Endpoints

@bp.route('', methods=['POST'])
@jwt_required()
def create_order():
    """Create a new order (buy or sell)."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"msg": "User not found or token invalid"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON in request"}), 400

    required_fields = ['order_type', 'quantity_kg', 'price_per_kg']
    for field in required_fields:
        if field not in data or data[field] is None:
            return jsonify({"msg": f"Missing required field: {field}"}), 400

    order_type = data['order_type'].lower()
    if order_type not in ['buy', 'sell']:
        return jsonify({"msg": "Invalid order_type. Must be 'buy' or 'sell'."}), 400

    hydrogen_product_id = data.get('hydrogen_product_id')
    if order_type == 'sell' and not hydrogen_product_id:
        # For this POC, a sell order must be linked to an existing product.
        # A more advanced system might allow creating a product implicitly or having unlisted sell offers.
        return jsonify({"msg": "Missing hydrogen_product_id for sell order. Sell orders must be against an existing product listing for this POC."}), 400
    
    if hydrogen_product_id:
        product = HydrogenProduct.query.get(hydrogen_product_id)
        if not product:
            return jsonify({"msg": f"HydrogenProduct with id {hydrogen_product_id} not found."}), 404
        if order_type == 'sell' and product.seller_id != current_user.id:
            return jsonify({"msg": "You can only create sell orders for your own products."}), 403


    try:
        order = Order(
            user_id=current_user.id,
            order_type=order_type,
            hydrogen_product_id=hydrogen_product_id,
            quantity_kg=Decimal(data['quantity_kg']),
            price_per_kg=Decimal(data['price_per_kg']),
            production_method_criteria=data.get('production_method_criteria'),
            location_criteria=data.get('location_criteria'),
            purity_criteria=Decimal(data.get('purity_criteria')) if data.get('purity_criteria') else None,
            max_ghg_intensity_criteria=Decimal(data.get('max_ghg_intensity_criteria')) if data.get('max_ghg_intensity_criteria') else None,
            status=data.get('status', 'pending'),
            expiration_timestamp=datetime.fromisoformat(data['expiration_timestamp']) if data.get('expiration_timestamp') else None
        )
        
        # Basic validation for sell orders against product quantity
        if order_type == 'sell' and product:
            if order.quantity_kg > product.quantity_kg: # Assuming product.quantity_kg is what's available
                 return jsonify({"msg": f"Sell order quantity ({order.quantity_kg}kg) cannot exceed available product quantity ({product.quantity_kg}kg)."}), 400


        db.session.add(order)
        db.session.commit()
        return jsonify(order.to_dict()), 201
    except InvalidOperation:
        return jsonify({"msg": "Invalid decimal value for quantity, price, purity, or GHG intensity."}), 400
    except ValueError as ve: # For date parsing errors
        return jsonify({"msg": f"Date format error: {str(ve)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to create order", "error": str(e)}), 500


@bp.route('', methods=['GET'])
@jwt_required()
def list_user_orders():
    """Get a list of orders made by the authenticated user."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"msg": "User not found or token invalid"}), 401
    
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return jsonify([order.to_dict() for order in orders]), 200


@bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Get details of a specific order."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"msg": "User not found or token invalid"}), 401

    order = Order.query.get_or_404(order_id)
    
    # Check if user owns the order or is an admin
    user_identity = get_jwt_identity()
    is_admin = 'admin' in user_identity.get('roles', [])

    if order.user_id != current_user.id and not is_admin:
        # If it's a sell order against a product, the product owner (seller) might also see it
        if order.order_type == 'sell' and order.product and order.product.seller_id == current_user.id:
            pass # Allow seller of the product to see sell orders against their product
        # If it's a buy order for a product, the product owner might also see it
        elif order.order_type == 'buy' and order.product and order.product.seller_id == current_user.id:
             pass # Allow seller of the product to see buy orders for their product
        else:
            return jsonify({"msg": "Not authorized to view this order"}), 403
            
    return jsonify(order.to_dict()), 200


@bp.route('/<int:order_id>', methods=['PUT'])
@jwt_required()
def update_order(order_id):
    """Update an order (e.g., change price, quantity), only if not yet matched."""
    current_user = get_current_user()
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        return jsonify({"msg": "Not authorized to update this order"}), 403

    # For POC, only allow updates if status is 'pending'
    if order.status != 'pending':
        return jsonify({"msg": f"Cannot update order. Order status is '{order.status}'."}), 400

    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON in request"}), 400

    try:
        if 'quantity_kg' in data: order.quantity_kg = Decimal(data['quantity_kg'])
        if 'price_per_kg' in data: order.price_per_kg = Decimal(data['price_per_kg'])
        if 'status' in data: # Be cautious allowing direct status updates - might be for cancellation
            new_status = data['status'].lower()
            if new_status == 'cancelled' and order.status == 'pending':
                order.status = new_status
            elif new_status != order.status: # Prevent arbitrary status changes
                 return jsonify({"msg": f"Updating status to '{new_status}' is not allowed or invalid transition."}), 400
        if 'expiration_timestamp' in data:
            order.expiration_timestamp = datetime.fromisoformat(data['expiration_timestamp']) if data.get('expiration_timestamp') else None

        # Re-validate sell order quantity if it's a sell order and quantity changes
        if order.order_type == 'sell' and order.product and 'quantity_kg' in data:
            if order.quantity_kg > order.product.quantity_kg: # Assuming product.quantity_kg is what's available
                 return jsonify({"msg": f"Sell order quantity ({order.quantity_kg}kg) cannot exceed available product quantity ({order.product.quantity_kg}kg)."}), 400


        db.session.commit()
        return jsonify(order.to_dict()), 200
    except InvalidOperation:
        return jsonify({"msg": "Invalid decimal value for quantity or price."}), 400
    except ValueError as ve: # For date parsing errors
        return jsonify({"msg": f"Date format error: {str(ve)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to update order", "error": str(e)}), 500


@bp.route('/<int:order_id>', methods=['DELETE'])
@jwt_required()
def cancel_order(order_id):
    """Cancel an order, only if not yet matched (changes status to 'cancelled')."""
    current_user = get_current_user()
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        return jsonify({"msg": "Not authorized to cancel this order"}), 403

    if order.status != 'pending' and order.status != 'partially_filled': # Allow cancelling partially filled orders too
        return jsonify({"msg": f"Cannot cancel order. Order status is '{order.status}'."}), 400
    
    try:
        order.status = 'cancelled'
        # Potentially, reverse any held quantities or credits here in a real system
        db.session.commit()
        return jsonify({"msg": "Order cancelled successfully", "order": order.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to cancel order", "error": str(e)}), 500

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import User, HydrogenProduct, db
from decimal import Decimal, InvalidOperation

bp = Blueprint('products', __name__)

def get_current_user():
    """Helper function to get the current authenticated user."""
    user_identity = get_jwt_identity()
    username = user_identity.get('username')
    return User.query.filter_by(username=username).first()

# Hydrogen Product (Listing) Endpoints

@bp.route('', methods=['POST'])
@jwt_required()
def create_hydrogen_product():
    """Create a new hydrogen product listing."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"msg": "User not found or token invalid"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON in request"}), 400

    required_fields = ['quantity_kg', 'price_per_kg', 'location_region', 'production_method']
    for field in required_fields:
        if field not in data or data[field] is None:
            return jsonify({"msg": f"Missing required field: {field}"}), 400

    try:
        product = HydrogenProduct(
            seller_id=current_user.id,
            quantity_kg=Decimal(data['quantity_kg']),
            price_per_kg=Decimal(data['price_per_kg']),
            location_region=data['location_region'],
            production_method=data['production_method'],
            purity_percentage=Decimal(data.get('purity_percentage')) if data.get('purity_percentage') else None,
            delivery_terms=data.get('delivery_terms'),
            ghg_intensity_kgco2e_per_kgh2=Decimal(data.get('ghg_intensity_kgco2e_per_kgh2')) if data.get('ghg_intensity_kgco2e_per_kgh2') else None,
            feedstock=data.get('feedstock'),
            energy_source=data.get('energy_source'),
            available_from_date=data.get('available_from_date'), # Add date parsing if necessary
            status=data.get('status', 'active')
        )
        db.session.add(product)
        db.session.commit()
        return jsonify(product.to_dict()), 201
    except InvalidOperation:
        return jsonify({"msg": "Invalid decimal value for quantity, price, purity, or GHG intensity."}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to create product", "error": str(e)}), 500


@bp.route('', methods=['GET'])
# @jwt_required() # Making this public for now, can be changed
def list_hydrogen_products():
    """Get a list of all available hydrogen products."""
    products = HydrogenProduct.query.filter_by(status='active').all() # Or filter as needed
    return jsonify([product.to_dict() for product in products]), 200


@bp.route('/<int:product_id>', methods=['GET'])
# @jwt_required() # Making this public for now
def get_hydrogen_product(product_id):
    """Get details of a specific hydrogen product."""
    product = HydrogenProduct.query.get_or_404(product_id)
    return jsonify(product.to_dict()), 200


@bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_hydrogen_product(product_id):
    """Update a hydrogen product listing."""
    current_user = get_current_user()
    product = HydrogenProduct.query.get_or_404(product_id)

    if product.seller_id != current_user.id:
        return jsonify({"msg": "Not authorized to update this product"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON in request"}), 400

    try:
        if 'quantity_kg' in data: product.quantity_kg = Decimal(data['quantity_kg'])
        if 'price_per_kg' in data: product.price_per_kg = Decimal(data['price_per_kg'])
        if 'location_region' in data: product.location_region = data['location_region']
        if 'production_method' in data: product.production_method = data['production_method']
        if 'purity_percentage' in data: product.purity_percentage = Decimal(data.get('purity_percentage')) if data.get('purity_percentage') is not None else None
        if 'delivery_terms' in data: product.delivery_terms = data.get('delivery_terms')
        if 'ghg_intensity_kgco2e_per_kgh2' in data: product.ghg_intensity_kgco2e_per_kgh2 = Decimal(data.get('ghg_intensity_kgco2e_per_kgh2')) if data.get('ghg_intensity_kgco2e_per_kgh2') is not None else None
        if 'feedstock' in data: product.feedstock = data.get('feedstock')
        if 'energy_source' in data: product.energy_source = data.get('energy_source')
        if 'available_from_date' in data: product.available_from_date = data.get('available_from_date') # Add date parsing
        if 'status' in data: product.status = data.get('status')

        db.session.commit()
        return jsonify(product.to_dict()), 200
    except InvalidOperation:
        return jsonify({"msg": "Invalid decimal value for quantity, price, purity, or GHG intensity."}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to update product", "error": str(e)}), 500


@bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_hydrogen_product(product_id):
    """Delete a hydrogen product listing."""
    current_user = get_current_user()
    product = HydrogenProduct.query.get_or_404(product_id)

    if product.seller_id != current_user.id:
        # Allow admin to delete as well
        user_identity = get_jwt_identity()
        if 'admin' not in user_identity.get('roles', []):
            return jsonify({"msg": "Not authorized to delete this product"}), 403
    
    # Check if product is part of any active orders - for POC, simple delete.
    # In full app, might change status to 'deleted' or handle related orders.
    try:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"msg": "Product deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to delete product", "error": str(e)}), 500

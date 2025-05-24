import pytest
from decimal import Decimal
from app.models import User, HydrogenProduct, Order, Trade # Import all models
from faker import Faker

fake = Faker()

# --- Product Listing Tests ---

def test_create_product_success(client, new_user_with_token):
    """Test successful creation of a hydrogen product."""
    user, token, _ = new_user_with_token
    product_data = {
        "quantity_kg": "1000.00",
        "price_per_kg": "5.50",
        "location_region": "North Europe",
        "production_method": "Electrolysis (Wind)",
        "purity_percentage": "99.99",
        "ghg_intensity_kgco2e_per_kgh2": "0.5",
        "feedstock": "Wind Power",
        "energy_source": "Dedicated Wind Farm",
        "available_from_date": fake.future_date(end_date="+30d").isoformat(),
    }
    response = client.post('/api/products', json=product_data, headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 201
    assert response.json['quantity_kg'] == product_data['quantity_kg']
    assert response.json['seller_id'] == user.id
    assert response.json['status'] == 'active'

    # Verify product in DB
    product_in_db = HydrogenProduct.query.get(response.json['id'])
    assert product_in_db is not None
    assert product_in_db.seller_id == user.id
    assert product_in_db.price_per_kg == Decimal(product_data['price_per_kg'])

def test_create_product_missing_fields(client, new_user_with_token):
    """Test creating product with missing required fields."""
    _, token, _ = new_user_with_token
    product_data = { # Missing quantity_kg, price_per_kg, etc.
        "location_region": "North Europe",
    }
    response = client.post('/api/products', json=product_data, headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 400
    assert "Missing required field" in response.json['msg']


def test_get_all_products_public(client, new_product): # new_product creates one product
    """Test retrieving all active products (public endpoint)."""
    # new_product fixture already creates a product
    product, _, _ = new_product
    
    response = client.get('/api/products')
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) >= 1 # At least one product from the fixture
    # Check if the created product is in the list
    found = any(p['id'] == product.id for p in response.json)
    assert found


def test_get_specific_product_public(client, new_product):
    """Test retrieving a specific product by ID (public endpoint)."""
    product, _, _ = new_product
    response = client.get(f'/api/products/{product.id}')
    assert response.status_code == 200
    assert response.json['id'] == product.id
    assert response.json['location_region'] == product.location_region

def test_get_nonexistent_product(client, init_database):
    """Test retrieving a nonexistent product."""
    response = client.get('/api/products/99999')
    assert response.status_code == 404 # Assuming @app.errorhandler(404) or get_or_404 is used

def test_update_own_product(client, new_product):
    """Test updating a product successfully by its owner."""
    product, seller, token = new_product
    update_data = {
        "quantity_kg": "800.00",
        "price_per_kg": "5.25",
        "status": "inactive"
    }
    response = client.put(f'/api/products/{product.id}', json=update_data, headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 200
    assert response.json['quantity_kg'] == "800.00"
    assert response.json['price_per_kg'] == "5.25"
    assert response.json['status'] == "inactive"

    db.session.refresh(product) # Refresh from DB
    assert product.quantity_kg == Decimal("800.00")
    assert product.status == "inactive"

def test_update_product_by_non_owner(client, new_product, new_user_with_token):
    """Test updating a product by someone other than the owner."""
    product_owned, _, _ = new_product # Product owned by one user
    _, other_user_token, _ = new_user_with_token # Token for a different user

    update_data = {"price_per_kg": "6.00"}
    response = client.put(f'/api/products/{product_owned.id}', json=update_data, headers={
        'Authorization': f'Bearer {other_user_token}' # Using other user's token
    })
    assert response.status_code == 403 # Forbidden


def test_delete_own_product(client, new_product):
    """Test deleting a product by its owner."""
    product, _, token = new_product
    response = client.delete(f'/api/products/{product.id}', headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 200
    assert "Product deleted successfully" in response.json['msg']
    assert HydrogenProduct.query.get(product.id) is None

# --- Order Creation Tests ---

def test_create_buy_order_success(client, new_user_with_token, new_product):
    """Test creating a buy order successfully."""
    buyer, token, _ = new_user_with_token
    product_to_buy, _, _ = new_product # Product available on the market

    # Ensure buyer is not the seller of product_to_buy
    if product_to_buy.seller_id == buyer.id:
        # Create a different seller and product if buyer is current product owner
        seller_user = User(username='test_seller_alt', email='seller_alt@example.com', password='password')
        db.session.add(seller_user)
        db.session.commit()
        product_to_buy = HydrogenProduct(seller_id=seller_user.id, quantity_kg=Decimal("500"), price_per_kg=Decimal("10"), location_region="alt_region", production_method="alt_method")
        db.session.add(product_to_buy)
        db.session.commit()


    order_data = {
        "order_type": "buy",
        "hydrogen_product_id": product_to_buy.id,
        "quantity_kg": "100.00",
        "price_per_kg": "5.00" # Buyer's bid price
    }
    response = client.post('/api/orders', json=order_data, headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 201
    assert response.json['order']['order_type'] == 'buy'
    assert response.json['order']['user_id'] == buyer.id
    assert response.json['order']['hydrogen_product_id'] == product_to_buy.id
    assert response.json['order']['status'] == 'pending' # Assuming no immediate match for this test

def test_create_sell_order_success(client, new_product):
    """Test creating a sell order successfully by the product owner."""
    product_to_sell, seller, token = new_product # product_to_sell is owned by seller

    order_data = {
        "order_type": "sell",
        "hydrogen_product_id": product_to_sell.id,
        "quantity_kg": "50.00", # Must be <= product_to_sell.quantity_kg
        "price_per_kg": product_to_sell.price_per_kg # Seller's ask price
    }
    response = client.post('/api/orders', json=order_data, headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 201
    assert response.json['order']['order_type'] == 'sell'
    assert response.json['order']['user_id'] == seller.id
    assert response.json['order']['status'] == 'pending'

def test_create_sell_order_for_unowned_product(client, new_user_with_token, new_product):
    """Test creating a sell order for a product not owned by the user."""
    # new_product creates a product owned by one user
    product_not_owned, _, _ = new_product
    
    # new_user_with_token provides another user and their token
    other_user, other_user_token, _ = new_user_with_token

    # Ensure other_user is not the owner of product_not_owned
    if product_not_owned.seller_id == other_user.id:
         pytest.skip("Fixture setup resulted in other_user owning the product, skipping test logic.")


    order_data = {
        "order_type": "sell",
        "hydrogen_product_id": product_not_owned.id,
        "quantity_kg": "10.00",
        "price_per_kg": "5.00"
    }
    response = client.post('/api/orders', json=order_data, headers={
        'Authorization': f'Bearer {other_user_token}' # Using other user's token
    })
    assert response.status_code == 403 # Forbidden
    assert "You can only create sell orders for your own products" in response.json['msg']

def test_create_sell_order_exceeding_product_quantity(client, new_product):
    """Test creating a sell order with quantity exceeding available product quantity."""
    product, seller, token = new_product
    order_data = {
        "order_type": "sell",
        "hydrogen_product_id": product.id,
        "quantity_kg": str(product.quantity_kg + Decimal("100")), # Exceeds available
        "price_per_kg": product.price_per_kg
    }
    response = client.post('/api/orders', json=order_data, headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 400
    assert "cannot exceed available product quantity" in response.json['msg'].lower()


# --- Order Matching Test (High-Level API Test) ---

def test_order_matching_creates_trade(client, init_database):
    """
    High-level test:
    1. Seller User 1 lists a product.
    2. Buyer User 2 places a buy order that should match.
    3. Verify Trade is created and statuses/quantities are updated.
    """
    db_instance = init_database

    # Create Seller (User 1)
    seller_data = {'username': 'seller_match_test', 'email': 'seller_mt@example.com', 'password': 'password'}
    seller_reg_resp = client.post('/api/auth/register', json=seller_data)
    assert seller_reg_resp.status_code == 201
    seller_token = seller_reg_resp.json['access_token']
    seller_id = seller_reg_resp.json['user']['id']

    # Seller lists a product
    product_spec = {
        "quantity_kg": "100.00", "price_per_kg": "8.00", "location_region": "EU-Central",
        "production_method": "Solar", "purity_percentage": "99.98"
    }
    product_resp = client.post('/api/products', json=product_spec, headers={'Authorization': f'Bearer {seller_token}'})
    assert product_resp.status_code == 201
    product_id = product_resp.json['id']
    original_product_quantity = Decimal(product_spec['quantity_kg'])

    # Seller creates a sell order for this product (to put it on the order book)
    sell_order_spec = {
        "order_type": "sell", "hydrogen_product_id": product_id,
        "quantity_kg": "70.00", "price_per_kg": "8.00" # Offering 70kg at $8.00
    }
    sell_order_resp = client.post('/api/orders', json=sell_order_spec, headers={'Authorization': f'Bearer {seller_token}'})
    assert sell_order_resp.status_code == 201
    sell_order_id = sell_order_resp.json['order']['id']
    assert sell_order_resp.json['order']['status'] == 'pending' # Should be pending as no buyer yet

    # Create Buyer (User 2)
    buyer_data = {'username': 'buyer_match_test', 'email': 'buyer_mt@example.com', 'password': 'password'}
    buyer_reg_resp = client.post('/api/auth/register', json=buyer_data)
    assert buyer_reg_resp.status_code == 201
    buyer_token = buyer_reg_resp.json['access_token']
    buyer_id = buyer_reg_resp.json['user']['id']

    # Buyer places a buy order that matches the seller's sell order
    buy_order_spec = {
        "order_type": "buy", "hydrogen_product_id": product_id,
        "quantity_kg": "50.00", # Buyer wants 50kg
        "price_per_kg": "8.10"  # Buyer is willing to pay up to $8.10 (matches $8.00 sell order)
    }
    buy_order_resp = client.post('/api/orders', json=buy_order_spec, headers={'Authorization': f'Bearer {buyer_token}'})
    
    assert buy_order_resp.status_code == 201
    buy_order_details = buy_order_resp.json['order']
    trades_made_details = buy_order_resp.json['trades_made']

    # Verify trade occurred
    assert len(trades_made_details) == 1
    trade_info = trades_made_details[0]
    assert Decimal(trade_info['quantity_traded_kg']) == Decimal("50.00")
    assert Decimal(trade_info['price_per_kg_agreed']) == Decimal("8.00") # Matched at sell order's price
    assert trade_info['buyer_id'] == buyer_id
    assert trade_info['seller_id'] == seller_id
    assert trade_info['hydrogen_product_id'] == product_id

    # Verify Order Statuses
    # Buyer's order should be 'filled'
    assert buy_order_details['status'] == 'filled'
    
    # Seller's sell order should be 'partially_filled' (70 offered, 50 sold)
    updated_sell_order_resp = client.get(f'/api/orders/{sell_order_id}', headers={'Authorization': f'Bearer {seller_token}'})
    assert updated_sell_order_resp.status_code == 200
    assert updated_sell_order_resp.json['status'] == 'partially_filled'
    assert Decimal(updated_sell_order_resp.json['quantity_kg']) == Decimal("20.00") # 70 - 50 remaining

    # Verify Product Quantity Update
    updated_product_resp = client.get(f'/api/products/{product_id}')
    assert updated_product_resp.status_code == 200
    assert Decimal(updated_product_resp.json['quantity_kg']) == original_product_quantity - Decimal("50.00") # 100 - 50
    assert updated_product_resp.json['status'] == 'active' # Still active as some quantity remains (from original 100kg)

    # Verify Trade record in DB (optional direct check)
    trade_in_db = Trade.query.get(trade_info['id'])
    assert trade_in_db is not None
    assert trade_in_db.buy_order_id == buy_order_details['id']
    assert trade_in_db.sell_order_id == sell_order_id

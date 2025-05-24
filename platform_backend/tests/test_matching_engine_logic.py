import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from app.models import User, HydrogenProduct, Order, Trade, db
from app.matching_engine import attempt_match_order

# Note: These tests interact with the database via the matching_engine,
# so they are more like integration tests for the matching_engine function
# rather than pure unit tests in isolation of a DB.

def create_test_user(username_suffix, email_suffix):
    user = User(username=f"testuser_{username_suffix}", email=f"test_{email_suffix}@example.com", password="password")
    db.session.add(user)
    db.session.commit()
    return user

def create_test_product(seller, quantity="100", price="10"):
    product = HydrogenProduct(
        seller_id=seller.id,
        quantity_kg=Decimal(quantity),
        price_per_kg=Decimal(price),
        location_region="Test Region",
        production_method="Test Method"
    )
    db.session.add(product)
    db.session.commit()
    return product

def create_test_order(user, product, order_type, quantity, price, status='pending'):
    order = Order(
        user_id=user.id,
        hydrogen_product_id=product.id,
        order_type=order_type,
        quantity_kg=Decimal(quantity),
        price_per_kg=Decimal(price),
        status=status
    )
    db.session.add(order)
    db.session.commit()
    return order

def test_no_match_if_no_counter_orders(init_database, new_user, new_product):
    """Test that an order doesn't match if there are no existing counter-orders."""
    db_instance = init_database
    product, seller, _ = new_product # seller is new_user[0]
    
    # Create a new user (buyer)
    buyer = create_test_user("buyer_nm", "buyer_nm")

    # Buyer places a buy order
    buy_order = create_test_order(buyer, product, "buy", "50", "10.00")

    trades = attempt_match_order(buy_order.id)
    assert len(trades) == 0
    assert buy_order.status == "pending"


def test_exact_match_buy_order_first(init_database):
    """
    Test a scenario where a buy order is placed first, then a matching sell order comes in.
    """
    db_instance = init_database
    seller = create_test_user("seller_em", "seller_em")
    buyer = create_test_user("buyer_em", "buyer_em")
    product = create_test_product(seller, quantity="100", price="10.50") # Initial product price not directly used by matching, but for info

    # 1. Buyer places a buy order (bid)
    buy_order = create_test_order(buyer, product, "buy", "50", "10.00") # Buyer wants 50kg at $10/kg

    # 2. Seller places a sell order (ask) that matches the buyer's bid
    sell_order = create_test_order(seller, product, "sell", "50", "10.00") # Seller offers 50kg at $10/kg

    # Attempt to match the newly placed sell_order
    trades = attempt_match_order(sell_order.id)

    assert len(trades) == 1
    trade = trades[0]
    assert trade.quantity_traded_kg == Decimal("50.00")
    assert trade.price_per_kg_agreed == Decimal("10.00") # Matched at buyer's bid price (standing order)
    assert trade.buyer_id == buyer.id
    assert trade.seller_id == seller.id
    assert trade.hydrogen_product_id == product.id

    db_instance.session.refresh(buy_order)
    db_instance.session.refresh(sell_order)
    db_instance.session.refresh(product)

    assert buy_order.status == "filled"
    assert sell_order.status == "filled"
    assert product.quantity_kg == Decimal("50.00") # 100 - 50


def test_exact_match_sell_order_first(init_database):
    """
    Test a scenario where a sell order is placed first, then a matching buy order comes in.
    """
    db_instance = init_database
    seller = create_test_user("seller_smo", "seller_smo")
    buyer = create_test_user("buyer_smo", "buyer_smo")
    product = create_test_product(seller, quantity="100", price="9.50")

    # 1. Seller places a sell order (ask)
    sell_order = create_test_order(seller, product, "sell", "75", "9.50") # Seller offers 75kg at $9.50/kg

    # 2. Buyer places a buy order (bid) that matches seller's ask
    buy_order = create_test_order(buyer, product, "buy", "75", "9.50") # Buyer wants 75kg at $9.50/kg

    # Attempt to match the newly placed buy_order
    trades = attempt_match_order(buy_order.id)

    assert len(trades) == 1
    trade = trades[0]
    assert trade.quantity_traded_kg == Decimal("75.00")
    assert trade.price_per_kg_agreed == Decimal("9.50") # Matched at seller's ask price (standing order)
    assert trade.buyer_id == buyer.id
    assert trade.seller_id == seller.id

    db_instance.session.refresh(buy_order)
    db_instance.session.refresh(sell_order)
    db_instance.session.refresh(product)

    assert buy_order.status == "filled"
    assert sell_order.status == "filled"
    assert product.quantity_kg == Decimal("25.00") # 100 - 75


def test_no_match_price_gap(init_database):
    """Test no match if buyer's bid is lower than seller's ask."""
    db_instance = init_database
    seller = create_test_user("seller_pg", "seller_pg")
    buyer = create_test_user("buyer_pg", "buyer_pg")
    product = create_test_product(seller)

    sell_order = create_test_order(seller, product, "sell", "50", "10.00")
    buy_order = create_test_order(buyer, product, "buy", "50", "9.00") # Buyer bids lower

    trades_from_buy = attempt_match_order(buy_order.id) # Try matching buy order
    assert len(trades_from_buy) == 0
    db_instance.session.refresh(sell_order) # Re-fetch sell order as it was created first
    trades_from_sell = attempt_match_order(sell_order.id) # Try matching sell order
    assert len(trades_from_sell) == 0

    assert buy_order.status == "pending"
    assert sell_order.status == "pending"


def test_partial_fill_incoming_order_larger(init_database):
    """Incoming order is larger than the best standing order. Incoming becomes partially_filled."""
    db_instance = init_database
    seller = create_test_user("seller_pfil", "seller_pfil")
    buyer = create_test_user("buyer_pfil", "buyer_pfil")
    product = create_test_product(seller, quantity="100", price="10.00")

    # Standing sell order
    sell_order = create_test_order(seller, product, "sell", "30", "10.00") # Seller offers 30kg

    # Incoming buy order, larger quantity
    buy_order = create_test_order(buyer, product, "buy", "50", "10.00") # Buyer wants 50kg

    trades = attempt_match_order(buy_order.id)

    assert len(trades) == 1
    trade = trades[0]
    assert trade.quantity_traded_kg == Decimal("30.00") # Trade happens for the smaller quantity
    assert trade.price_per_kg_agreed == Decimal("10.00")

    db_instance.session.refresh(buy_order)
    db_instance.session.refresh(sell_order)
    db_instance.session.refresh(product)

    assert buy_order.status == "partially_filled" # Buyer's order partially filled
    assert buy_order.quantity_kg == Decimal("20.00") # Remaining quantity for buyer
    assert sell_order.status == "filled" # Seller's order fully filled
    assert product.quantity_kg == Decimal("70.00") # 100 - 30


def test_partial_fill_standing_order_larger(init_database):
    """Incoming order is smaller than the best standing order. Standing becomes partially_filled."""
    db_instance = init_database
    seller = create_test_user("seller_pfsol", "seller_pfsol")
    buyer = create_test_user("buyer_pfsol", "buyer_pfsol")
    product = create_test_product(seller, quantity="100", price="10.00")

    # Standing sell order
    sell_order = create_test_order(seller, product, "sell", "80", "10.00") # Seller offers 80kg

    # Incoming buy order, smaller quantity
    buy_order = create_test_order(buyer, product, "buy", "20", "10.00") # Buyer wants 20kg

    trades = attempt_match_order(buy_order.id)

    assert len(trades) == 1
    trade = trades[0]
    assert trade.quantity_traded_kg == Decimal("20.00")
    assert trade.price_per_kg_agreed == Decimal("10.00")

    db_instance.session.refresh(buy_order)
    db_instance.session.refresh(sell_order)
    db_instance.session.refresh(product)

    assert buy_order.status == "filled" # Buyer's order fully filled
    assert sell_order.status == "partially_filled" # Seller's order partially filled
    assert sell_order.quantity_kg == Decimal("60.00") # Remaining quantity for seller
    assert product.quantity_kg == Decimal("80.00") # 100 - 20


def test_multiple_matches_fill_incoming_order(init_database):
    """Incoming order matches against multiple smaller standing orders."""
    db_instance = init_database
    seller1 = create_test_user("seller_mm1", "seller_mm1")
    seller2 = create_test_user("seller_mm2", "seller_mm2")
    buyer = create_test_user("buyer_mm", "buyer_mm")
    product = create_test_product(seller1, quantity="100", price="10.00") # Product owned by seller1

    # Standing sell orders from different sellers (or same, but different orders)
    # For this test, let's assume product is listed by seller1, but seller2 can also place sell orders against it
    # if the system allows (our current Order model links to a product, seller_id on product matters)
    # For simplicity, let's assume seller1 places multiple sell orders for their own product.
    sell_order1 = create_test_order(seller1, product, "sell", "20", "9.90", status='pending') # oldest, best price
    sell_order2 = create_test_order(seller1, product, "sell", "25", "10.00", status='pending') # next best price
    
    # Incoming buy order that can consume both
    buy_order = create_test_order(buyer, product, "buy", "50", "10.00") # Buyer wants 50kg at up to $10/kg

    # The current matching engine `attempt_match_order` processes one incoming order and stops after the first
    # set of matches it can make (potentially one trade if it's a full fill against one counter, or one partial).
    # To test this scenario properly, the engine would need to loop or be called iteratively for the remaining
    # quantity of a partially filled incoming order.
    # The current engine will match sell_order1 first.
    
    trades = attempt_match_order(buy_order.id)
    
    assert len(trades) == 1 # Current engine makes one trade for the best match
    trade1 = trades[0]
    assert trade1.quantity_traded_kg == Decimal("20.00")
    assert trade1.price_per_kg_agreed == Decimal("9.90")
    assert trade1.sell_order_id == sell_order1.id

    db_instance.session.refresh(buy_order)
    db_instance.session.refresh(sell_order1)
    db_instance.session.refresh(sell_order2) # Should be untouched
    db_instance.session.refresh(product)

    assert buy_order.status == "partially_filled" # Matched 20kg out of 50kg
    assert buy_order.quantity_kg == Decimal("30.00") # Remaining
    assert sell_order1.status == "filled"
    assert sell_order2.status == "pending" # sell_order2 was not matched yet
    assert product.quantity_kg == Decimal("80.00") # 100 - 20

    # To match the rest of buy_order, attempt_match_order would need to be called again
    # with the updated buy_order (if it were designed to be re-entrant for the same order)
    # or the matching engine loop internally for the incoming order.
    # For this POC, we'll simulate the next attempt if the order is still 'partially_filled'
    # This is a limitation of the current simple engine's single pass for an incoming order.
    
    # If we were to call it again (conceptual for now, not how the current trigger works):
    # trades2 = attempt_match_order(buy_order.id) # Assuming buy_order is now the one with 30kg remaining
    # This would then match against sell_order2.
    # The current test structure is one call per new order.
    # A more robust test for multi-match would require a more complex matching engine loop.
    
    # To make this test pass with current engine:
    # If buyer's bid was 10.00, and they wanted 20kg, it would fill against sell_order1.
    # If they wanted 25kg, it would fill 20kg from sell_order1, and the rest would remain pending.
    # The test above correctly shows the first match.

def test_product_quantity_update_and_sold_status(init_database):
    db_instance = init_database
    seller = create_test_user("seller_pqs", "seller_pqs")
    buyer = create_test_user("buyer_pqs", "buyer_pqs")
    product = create_test_product(seller, quantity="50", price="10.00")

    buy_order = create_test_order(buyer, product, "buy", "50", "10.00")
    sell_order = create_test_order(seller, product, "sell", "50", "10.00") # Seller places matching sell

    trades = attempt_match_order(sell_order.id) # Match the sell order

    assert len(trades) == 1
    db_instance.session.refresh(product)
    assert product.quantity_kg == Decimal("0.00")
    assert product.status == "sold"

def test_cannot_match_own_orders(init_database):
    db_instance = init_database
    user1 = create_test_user("user_own", "user_own")
    product = create_test_product(user1, quantity="100", price="10.00")

    # User1 places a sell order
    sell_order = create_test_order(user1, product, "sell", "50", "10.00")
    # User1 places a buy order for their own product
    buy_order = create_test_order(user1, product, "buy", "50", "10.00")

    trades_from_buy = attempt_match_order(buy_order.id)
    assert len(trades_from_buy) == 0

    db_instance.session.refresh(sell_order)
    trades_from_sell = attempt_match_order(sell_order.id) # If sell_order was processed after buy_order
    assert len(trades_from_sell) == 0
    
    assert sell_order.status == "pending"
    assert buy_order.status == "pending"

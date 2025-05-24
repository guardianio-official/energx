from .models import db, Order, Trade, HydrogenProduct
from sqlalchemy import and_, or_
from decimal import Decimal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def attempt_match_order(incoming_order_id):
    """
    Attempts to match a newly placed order with existing orders in the order book.
    This function is the core of the matching engine for the POC.

    Args:
        incoming_order_id (int): The ID of the newly placed order to match.

    Returns:
        list[Trade]: A list of Trade objects created, or an empty list if no matches.
    """
    trades_created = []
    
    with db.session.begin_nested(): # Use nested transaction for matching logic
        incoming_order = db.session.get(Order, incoming_order_id)

        if not incoming_order or incoming_order.status != 'pending':
            logger.info(f"Order {incoming_order_id} not found or not in 'pending' state. No matching attempted.")
            return trades_created

        logger.info(f"Attempting to match order ID: {incoming_order.id}, Type: {incoming_order.order_type}, Product ID: {incoming_order.hydrogen_product_id}, Qty: {incoming_order.quantity_kg}, Price: {incoming_order.price_per_kg}")

        # For this POC, matching is primarily based on a specific HydrogenProduct ID.
        # Buy orders without a specific product_id (criteria-based) are not matched by this simple engine.
        if not incoming_order.hydrogen_product_id:
            logger.info(f"Incoming order {incoming_order.id} is a criteria-based buy order. Simple matching engine requires a specific product ID.")
            return trades_created

        if incoming_order.order_type == 'buy':
            # Incoming is a BUY order, look for SELL orders (asks)
            # Match criteria:
            # 1. Same HydrogenProduct ID
            # 2. Sell order price (ask_price) <= Buy order price (bid_price)
            # 3. Order status is 'pending'
            # Order by price (lowest sell price first - best for buyer), then by time (oldest first)
            potential_matches = db.session.query(Order).filter(
                Order.hydrogen_product_id == incoming_order.hydrogen_product_id,
                Order.order_type == 'sell',
                Order.price_per_kg <= incoming_order.price_per_kg,
                Order.status == 'pending',
                Order.user_id != incoming_order.user_id # Cannot match with own orders
            ).order_by(Order.price_per_kg.asc(), Order.created_timestamp.asc()).all()

        elif incoming_order.order_type == 'sell':
            # Incoming is a SELL order, look for BUY orders (bids)
            # Match criteria:
            # 1. Same HydrogenProduct ID
            # 2. Buy order price (bid_price) >= Sell order price (ask_price)
            # 3. Order status is 'pending'
            # Order by price (highest buy price first - best for seller), then by time (oldest first)
            potential_matches = db.session.query(Order).filter(
                Order.hydrogen_product_id == incoming_order.hydrogen_product_id,
                Order.order_type == 'buy',
                Order.price_per_kg >= incoming_order.price_per_kg,
                Order.status == 'pending',
                Order.user_id != incoming_order.user_id # Cannot match with own orders
            ).order_by(Order.price_per_kg.desc(), Order.created_timestamp.asc()).all()
        else:
            logger.error(f"Unknown order type for order {incoming_order.id}: {incoming_order.order_type}")
            return trades_created # Should not happen

        if not potential_matches:
            logger.info(f"No potential matches found for order {incoming_order.id}.")
            return trades_created

        logger.info(f"Found {len(potential_matches)} potential match(es) for order {incoming_order.id}.")

        # --- Simplified Full Fill Logic for POC ---
        # This POC will only attempt full fills. If the oldest, best-priced counter-order
        # has exactly the required quantity, a trade occurs. Partial fills are a future enhancement.

        for counter_order in potential_matches:
            if incoming_order.status != 'pending': # If incoming order got filled by a previous match in this loop
                break 

            logger.info(f"Considering counter-order ID: {counter_order.id}, Qty: {counter_order.quantity_kg}, Price: {counter_order.price_per_kg}")

            # For POC: Exact quantity match.
            # Future: Allow partial fills. If incoming_order.quantity_kg == counter_order.quantity_kg:
            trade_quantity = min(incoming_order.quantity_kg, counter_order.quantity_kg) # For future partial fills

            # For POC, we'll simplify and assume we try to fill the incoming order's quantity.
            # If counter_order quantity is less, it's a partial fill (not fully handled in POC status updates)
            # If counter_order quantity is more, incoming is filled, counter_order is partially filled.

            if trade_quantity > 0: # A match can occur
                # Execution Price: For POC, use the price of the standing order (the one already in the book).
                # Could also be incoming_order.price_per_kg, or a mid-price. This is a business rule.
                execution_price = counter_order.price_per_kg
                if incoming_order.order_type == 'sell': # If incoming is sell, counter is buy
                    execution_price = counter_order.price_per_kg # Buyer's bid price
                elif incoming_order.order_type == 'buy': # If incoming is buy, counter is sell
                    execution_price = counter_order.price_per_kg # Seller's ask price
                
                logger.info(f"Potential match found between Order {incoming_order.id} and Order {counter_order.id} for {trade_quantity} kg at {execution_price} price.")

                # --- Create Trade ---
                buy_order_obj = incoming_order if incoming_order.order_type == 'buy' else counter_order
                sell_order_obj = incoming_order if incoming_order.order_type == 'sell' else counter_order

                trade = Trade(
                    buy_order_id=buy_order_obj.id,
                    sell_order_id=sell_order_obj.id,
                    hydrogen_product_id=incoming_order.hydrogen_product_id, # Both orders share this
                    quantity_traded_kg=trade_quantity,
                    price_per_kg_agreed=execution_price,
                    buyer_id=buy_order_obj.user_id,
                    seller_id=sell_order_obj.user_id,
                    settlement_status='pending' # Default for POC
                )
                db.session.add(trade)
                trades_created.append(trade)
                logger.info(f"Trade record created: {trade}")

                # --- Update Order Statuses and Quantities ---
                # For POC: Assuming full fill of the smaller quantity.
                # If incoming_order.quantity_kg == counter_order.quantity_kg -> both FILLED
                # If incoming_order.quantity_kg < counter_order.quantity_kg -> incoming FILLED, counter PARTIALLY_FILLED
                # If incoming_order.quantity_kg > counter_order.quantity_kg -> incoming PARTIALLY_FILLED, counter FILLED

                # Update incoming order
                if incoming_order.quantity_kg == trade_quantity:
                    incoming_order.status = 'filled'
                elif incoming_order.quantity_kg > trade_quantity:
                    incoming_order.status = 'partially_filled' # Mark as such, but simple engine stops for this order
                    incoming_order.quantity_kg -= trade_quantity # Remaining quantity
                # else: should not happen if trade_quantity is min

                # Update counter order
                if counter_order.quantity_kg == trade_quantity:
                    counter_order.status = 'filled'
                elif counter_order.quantity_kg > trade_quantity:
                    counter_order.status = 'partially_filled'
                    counter_order.quantity_kg -= trade_quantity # Remaining quantity
                
                db.session.add(incoming_order)
                db.session.add(counter_order)
                logger.info(f"Order {incoming_order.id} status: {incoming_order.status}, remaining qty: {incoming_order.quantity_kg}")
                logger.info(f"Order {counter_order.id} status: {counter_order.status}, remaining qty: {counter_order.quantity_kg}")


                # --- Update HydrogenProduct Quantity ---
                product = db.session.get(HydrogenProduct, incoming_order.hydrogen_product_id)
                if product:
                    if product.quantity_kg >= trade_quantity:
                        product.quantity_kg -= trade_quantity
                        logger.info(f"Product {product.id} quantity updated. New available quantity: {product.quantity_kg}")
                        if product.quantity_kg == 0:
                            product.status = 'sold' # Mark product as sold out
                            logger.info(f"Product {product.id} marked as sold out.")
                        db.session.add(product)
                    else:
                        logger.error(f"Not enough quantity for product {product.id} to fulfill trade of {trade_quantity}kg. Available: {product.quantity_kg}kg. This indicates a potential issue.")
                        # This should ideally be caught earlier or handled with more robust quantity checks.
                        # For POC, log and continue, but this trade might fail or be inconsistent.
                        # Could raise an exception here to rollback the specific trade attempt.
                        # db.session.rollback() # Rollback this specific trade attempt
                        # trades_created.pop() # Remove the last trade
                        # continue
                
                # For this POC, we assume one match is sufficient to process for the incoming order.
                # A more complex engine would continue if the incoming order is 'partially_filled'.
                if incoming_order.status == 'filled' or incoming_order.status == 'partially_filled':
                     # If incoming order is filled or partially filled (and we stop for now), commit and exit loop.
                    # A real engine might try to fill the remaining part of a partially_filled incoming order.
                    break 
        
        if trades_created:
            try:
                db.session.commit() # Commit the transaction for all successful matches in this run
                logger.info(f"Successfully committed {len(trades_created)} trade(s).")
                # --- Placeholder for Notification System ---
                # For each trade in trades_created:
                #   - Notify buyer (trade.buyer_id)
                #   - Notify seller (trade.seller_id)
                #   Notification could be an email, an in-app message, or a webhook event.
                #   Example: notification_service.send_trade_confirmation(trade)
                logger.info("Placeholder: Notifications would be sent for successful trades here.")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error committing trades to database: {e}")
                return [] # Return empty if commit fails
        else:
            # No trades were made, so no explicit commit needed for trades, but rollback if any changes made
            # (though there shouldn't be if no trades were appended)
            db.session.rollback()


    return trades_created


def get_order_book_for_product(product_id):
    """
    Retrieves the current order book (pending buy and sell orders) for a specific product.
    This is more for informational purposes or for a UI to display.
    """
    buy_orders = Order.query.filter(
        Order.hydrogen_product_id == product_id,
        Order.order_type == 'buy',
        Order.status == 'pending'
    ).order_by(Order.price_per_kg.desc(), Order.created_timestamp.asc()).all()

    sell_orders = Order.query.filter(
        Order.hydrogen_product_id == product_id,
        Order.order_type == 'sell',
        Order.status == 'pending'
    ).order_by(Order.price_per_kg.asc(), Order.created_timestamp.asc()).all()

    return {
        "product_id": product_id,
        "bids": [order.to_dict() for order in buy_orders],
        "asks": [order.to_dict() for order in sell_orders]
    }

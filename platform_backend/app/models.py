from . import db, bcrypt # Import db and bcrypt from the app package

class User(db.Model):
    """
    User model based on data_models.md
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    organization_name = db.Column(db.String(120), nullable=True)
    # For roles, using a simple string for POC. A separate Role model and many-to-many relationship
    # would be better for a production system (e.g., UserRoles table).
    roles = db.Column(db.String(80), nullable=True, default='user') # e.g., "user,admin"
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    def __init__(self, username, email, password, organization_name=None, roles='user'):
        self.username = username
        self.email = email
        self.set_password(password)
        self.organization_name = organization_name
        self.roles = roles

    def set_password(self, password):
        """Hashes the password and stores it."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Returns user data as a dictionary, excluding sensitive information."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'organization_name': self.organization_name,
            'roles': self.roles.split(',') if self.roles else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<User {self.username}>'


class HydrogenProduct(db.Model):
    """
    HydrogenProduct model based on data_models.md
    Represents a specific batch or offer of hydrogen available for sale.
    """
    __tablename__ = 'hydrogen_products'

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quantity_kg = db.Column(db.Numeric(10, 2), nullable=False)
    price_per_kg = db.Column(db.Numeric(10, 2), nullable=False)
    location_region = db.Column(db.String(100), nullable=False)
    location_plant_id = db.Column(db.String(100), nullable=True)
    production_method = db.Column(db.String(100), nullable=False) # Consider ENUM for production
    purity_percentage = db.Column(db.Numeric(5, 3), nullable=True)
    delivery_terms = db.Column(db.Text, nullable=True)
    ghg_intensity_kgco2e_per_kgh2 = db.Column(db.Numeric(10, 4), nullable=True)
    feedstock = db.Column(db.String(100), nullable=True)
    energy_source = db.Column(db.String(100), nullable=True)
    available_from_date = db.Column(db.Date, nullable=True)
    listing_timestamp = db.Column(db.DateTime, server_default=db.func.now())
    updated_timestamp = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    status = db.Column(db.String(50), default='active') # e.g., "active", "inactive", "sold", "expired"

    seller = db.relationship('User', backref=db.backref('hydrogen_products', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'seller_id': self.seller_id,
            'seller_username': self.seller.username if self.seller else None,
            'quantity_kg': str(self.quantity_kg) if self.quantity_kg else None,
            'price_per_kg': str(self.price_per_kg) if self.price_per_kg else None,
            'location_region': self.location_region,
            'location_plant_id': self.location_plant_id,
            'production_method': self.production_method,
            'purity_percentage': str(self.purity_percentage) if self.purity_percentage else None,
            'delivery_terms': self.delivery_terms,
            'ghg_intensity_kgco2e_per_kgh2': str(self.ghg_intensity_kgco2e_per_kgh2) if self.ghg_intensity_kgco2e_per_kgh2 else None,
            'feedstock': self.feedstock,
            'energy_source': self.energy_source,
            'available_from_date': self.available_from_date.isoformat() if self.available_from_date else None,
            'listing_timestamp': self.listing_timestamp.isoformat() if self.listing_timestamp else None,
            'updated_timestamp': self.updated_timestamp.isoformat() if self.updated_timestamp else None,
            'status': self.status
        }

    def __repr__(self):
        return f'<HydrogenProduct {self.id} by User {self.seller_id}>'


class Order(db.Model):
    """
    Order model based on data_models.md
    Represents a buy or sell intention placed by a user.
    """
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # The user placing the order
    order_type = db.Column(db.String(10), nullable=False)  # "buy" or "sell"
    # For sell orders, this links to a specific product.
    # For buy orders, this might be null if buying based on criteria.
    hydrogen_product_id = db.Column(db.Integer, db.ForeignKey('hydrogen_products.id'), nullable=True)
    quantity_kg = db.Column(db.Numeric(10, 2), nullable=False)
    price_per_kg = db.Column(db.Numeric(10, 2), nullable=False) # Bid price for buy, Ask price for sell

    # Criteria fields (mostly for buy orders, but can be generic if needed)
    production_method_criteria = db.Column(db.String(255), nullable=True) # Comma-separated list or JSON
    location_criteria = db.Column(db.String(100), nullable=True)
    purity_criteria = db.Column(db.Numeric(5, 3), nullable=True)
    max_ghg_intensity_criteria = db.Column(db.Numeric(10, 4), nullable=True)

    status = db.Column(db.String(50), default='pending') # "pending", "partially_filled", "filled", "cancelled", "expired"
    created_timestamp = db.Column(db.DateTime, server_default=db.func.now())
    updated_timestamp = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    expiration_timestamp = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    product = db.relationship('HydrogenProduct', backref=db.backref('orders', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'order_placer_username': self.user.username if self.user else None,
            'order_type': self.order_type,
            'hydrogen_product_id': self.hydrogen_product_id,
            'quantity_kg': str(self.quantity_kg) if self.quantity_kg else None,
            'price_per_kg': str(self.price_per_kg) if self.price_per_kg else None,
            'production_method_criteria': self.production_method_criteria,
            'location_criteria': self.location_criteria,
            'purity_criteria': str(self.purity_criteria) if self.purity_criteria else None,
            'max_ghg_intensity_criteria': str(self.max_ghg_intensity_criteria) if self.max_ghg_intensity_criteria else None,
            'status': self.status,
            'created_timestamp': self.created_timestamp.isoformat() if self.created_timestamp else None,
            'updated_timestamp': self.updated_timestamp.isoformat() if self.updated_timestamp else None,
            'expiration_timestamp': self.expiration_timestamp.isoformat() if self.expiration_timestamp else None
        }

    def __repr__(self):
        return f'<Order {self.id} ({self.order_type}) by User {self.user_id}>'


class Trade(db.Model):
    """
    Trade model based on data_models.md
    Represents a consummated transaction between a buyer and a seller.
    """
    __tablename__ = 'trades'

    id = db.Column(db.Integer, primary_key=True)
    # Link to the buy and sell orders that formed this trade
    buy_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    sell_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)

    hydrogen_product_id = db.Column(db.Integer, db.ForeignKey('hydrogen_products.id'), nullable=False)
    quantity_traded_kg = db.Column(db.Numeric(10, 2), nullable=False)
    price_per_kg_agreed = db.Column(db.Numeric(10, 2), nullable=False) # Execution price
    trade_timestamp = db.Column(db.DateTime, server_default=db.func.now())
    # For POC, settlement might be implicit or handled externally.
    settlement_status = db.Column(db.String(50), default='pending') # "pending", "completed", "failed"

    # Relationships to access the Order and Product objects
    # Using foreign_keys to specify which relationship corresponds to which ForeignKey constraint
    # when there are multiple FKs to the same table (orders).
    buy_order = db.relationship('Order', foreign_keys=[buy_order_id], backref=db.backref('trades_as_buy', lazy='dynamic'))
    sell_order = db.relationship('Order', foreign_keys=[sell_order_id], backref=db.backref('trades_as_sell', lazy='dynamic'))
    product = db.relationship('HydrogenProduct', backref=db.backref('trades', lazy='dynamic'))

    # Storing buyer and seller ID directly for easier querying on trade history,
    # though it can be derived from the orders.
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    buyer = db.relationship('User', foreign_keys=[buyer_id], backref=db.backref('trades_as_buyer', lazy='dynamic'))
    seller = db.relationship('User', foreign_keys=[seller_id], backref=db.backref('trades_as_seller', lazy='dynamic'))


    def to_dict(self):
        return {
            'id': self.id,
            'buy_order_id': self.buy_order_id,
            'sell_order_id': self.sell_order_id,
            'hydrogen_product_id': self.hydrogen_product_id,
            'product_details': self.product.to_dict() if self.product else None,
            'quantity_traded_kg': str(self.quantity_traded_kg),
            'price_per_kg_agreed': str(self.price_per_kg_agreed),
            'trade_timestamp': self.trade_timestamp.isoformat() if self.trade_timestamp else None,
            'settlement_status': self.settlement_status,
            'buyer_id': self.buyer_id,
            'buyer_username': self.buyer.username if self.buyer else None,
            'seller_id': self.seller_id,
            'seller_username': self.seller.username if self.seller else None,
        }

    def __repr__(self):
        return f'<Trade {self.id} - Product {self.hydrogen_product_id} - {self.quantity_traded_kg}kg @ {self.price_per_kg_agreed}/kg>'

# Potential future models (based on data_models.md, not implemented in this subtask)
# class EnvironmentalCredit(db.Model): ...

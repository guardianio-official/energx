import pytest
import os
from app import create_app, db
from app.models import User, HydrogenProduct, Order, Trade # Import all models
from faker import Faker

# Initialize Faker for generating test data
fake = Faker()

@pytest.fixture(scope='session')
def app():
    """
    Session-wide test Flask application.
    Configured for testing with an in-memory SQLite database.
    """
    # Set testing environment variables
    # Note: For a real PostgreSQL test setup, you'd point to a test PG database.
    # Using SQLite for simplicity in this POC.
    os.environ['FLASK_ENV'] = 'testing'
    
    # Construct path for SQLite in-memory or a test file db
    # For in-memory: SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # For a file-based test db (gets cleaned up):
    # temp_db_path = os.path.join(os.path.dirname(__file__), 'test_app.db')
    # SQLALCHEMY_DATABASE_URI = f"sqlite:///{temp_db_path}"

    # For this POC, we'll modify the app config directly if create_app doesn't easily allow override
    # This is a common pattern, but ideally, create_app would take a config object or name.
    
    app_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': "sqlite:///:memory:", # In-memory SQLite for tests
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-secret-key', # Use a fixed secret for tests
        'BCRYPT_LOG_ROUNDS': 4, # Speed up hashing for tests
        'WTF_CSRF_ENABLED': False, # Disable CSRF for forms if any (not typical for API tests)
    }

    app_instance = create_app() # create_app should ideally take test_config
    
    # Override config for testing
    app_instance.config.update(app_config)

    # Ensure the app context is pushed so that db operations can be performed.
    with app_instance.app_context():
        db.create_all() # Create database tables for our test DB

    yield app_instance # provide the app instance for the test session

    # Teardown:
    with app_instance.app_context():
        db.session.remove()
        db.drop_all() # Drop all tables
    # if os.path.exists(temp_db_path):
    #     os.unlink(temp_db_path) # Remove test db file if one was created


@pytest.fixture() # Default scope is 'function'
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture()
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def init_database(app):
    """
    Function-scoped fixture to ensure a clean database for each test.
    It creates all tables, yields, and then drops all tables.
    This is an alternative to session-scoped app if tests modify db and need isolation.
    For the current session-scoped app, this might be redundant if tests clean up after themselves
    or if using transactions. Let's refine this to manage data per test.
    """
    with app.app_context():
        # db.create_all() # Tables are created by the app fixture for the session

        yield db # provide the database connection

        # Clean up: remove all data from tables after each test
        # This is often preferred over drop_all/create_all per test for speed.
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        # db.session.remove()
        # db.drop_all()


@pytest.fixture(scope='function')
def new_user(init_database):
    """Fixture to create a new user and add it to the test database."""
    db_instance = init_database
    user_data = {
        'username': fake.user_name(),
        'email': fake.email(),
        'password': 'testpassword123' # Plain password, will be hashed by model
    }
    user = User(
        username=user_data['username'],
        email=user_data['email'],
        password=user_data['password'],
        organization_name=fake.company()
    )
    db_instance.session.add(user)
    db_instance.session.commit()
    # Return all data needed for tests, including plain password for login tests
    return user, user_data['password']


@pytest.fixture(scope='function')
def new_user_with_token(client, new_user):
    """Fixture to create a new user and get an auth token for them."""
    user_obj, plain_password = new_user
    response = client.post('/api/auth/login', json={
        'identifier': user_obj.email,
        'password': plain_password
    })
    assert response.status_code == 200
    token = response.json['access_token']
    return user_obj, token, plain_password

# Fixture for creating a product (can be used by multiple tests)
@pytest.fixture(scope='function')
def new_product(init_database, new_user_with_token):
    db_instance = init_database
    seller, token, _ = new_user_with_token

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
    
    product = HydrogenProduct(
        seller_id=seller.id,
        quantity_kg=product_data['quantity_kg'],
        price_per_kg=product_data['price_per_kg'],
        location_region=product_data['location_region'],
        production_method=product_data['production_method'],
        purity_percentage=product_data.get('purity_percentage'),
        ghg_intensity_kgco2e_per_kgh2=product_data.get('ghg_intensity_kgco2e_per_kgh2'),
        feedstock=product_data.get('feedstock'),
        energy_source=product_data.get('energy_source'),
        available_from_date=product_data.get('available_from_date')
    )
    db_instance.session.add(product)
    db_instance.session.commit()
    return product, seller, token # Return product and the seller with their token

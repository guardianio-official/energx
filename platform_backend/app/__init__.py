import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS # Import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)

    # Enable CORS
    # For POC, allow all origins. For production, restrict to specific frontend URL.
    # The frontend dev server typically runs on http://localhost:3000 or http://localhost:5173 (Vite default)
    # VITE_API_BASE_URL will be like http://localhost:5000/api, so requests come from the frontend origin.
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:5173"]}})

    # Configuration
    # Configuration for PostgreSQL
    # DATABASE_URL format: postgresql://user:password@host:port/dbname
    # Default to SQLite if DATABASE_URL is not fully set for PostgreSQL, for backward compatibility or simpler local non-Docker setup.
    pg_user = os.environ.get('DB_USER')
    pg_password = os.environ.get('DB_PASSWORD')
    pg_host = os.environ.get('DB_HOST')
    pg_port = os.environ.get('DB_PORT')
    pg_name = os.environ.get('DB_NAME')

    if pg_user and pg_password and pg_host and pg_port and pg_name:
        app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_name}"
    else:
        # Fallback to SQLite if PostgreSQL env vars are not set
        # Ensure the instance folder exists for SQLite
        try:
            os.makedirs(app.instance_path)
        except OSError:
            pass # Already exists
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'ghexchange_fallback.db')
        app.logger.warning("PostgreSQL environment variables not fully set. Falling back to SQLite.")


    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secret-key-for-poc') # Change this in production!
    app.config['BCRYPT_LOG_ROUNDS'] = 12 # Configuration for Bcrypt

    # Initialize extensions    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)

    # Register Blueprints
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from .user import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/api/user')

    from .products import bp as products_bp
    app.register_blueprint(products_bp, url_prefix='/api/products')

    from .orders import bp as orders_bp
    app.register_blueprint(orders_bp, url_prefix='/api/orders')

    from .trades import bp as trades_bp
    app.register_blueprint(trades_bp, url_prefix='/api/trades')

    @app.route('/health')
    def health_check():
        return "OK", 200

    return app

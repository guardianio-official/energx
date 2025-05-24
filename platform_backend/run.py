from app import create_app, db
from app.models import User, HydrogenProduct, Order, Trade # Import models to ensure they are known to Flask-Migrate

# Create the Flask app instance
app = create_app()

# This context is useful for Flask-Migrate and for running a Flask shell
# with the app context.
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'HydrogenProduct': HydrogenProduct, 'Order': Order, 'Trade': Trade}

if __name__ == '__main__':
    # Note: For development, Flask's built-in server is fine.
    # For production, use a WSGI server like Gunicorn or uWSGI.
    app.run(debug=True) # debug=True is not for production use.

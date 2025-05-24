# Green Hydrogen Exchange - Backend Platform

This directory contains the Flask backend API for the Green Hydrogen Exchange platform.

## Prerequisites

*   Python (v3.8 or later recommended)
*   pip (Python package installer)
*   Virtual environment tool (e.g., `venv`)

## Environment Variables

The backend uses a `.env` file to manage configuration. Create a file named `.env` in the `platform_backend/` directory. A basic template is:

```env
# Flask Environment Variables
FLASK_APP=run.py
FLASK_ENV=development # Change to 'production' for production
DEBUG=True # Change to False for production

# Database URL
# For SQLite (used in this POC for simplicity):
DATABASE_URL="sqlite:///instance/ghexchange.db"
# For PostgreSQL (recommended for production):
# DATABASE_URL="postgresql://user:password@host:port/dbname"

# JWT Secret Key - CHANGE THIS TO A STRONG, RANDOM KEY IN PRODUCTION
JWT_SECRET_KEY="your-super-secret-and-complex-jwt-key-please-change"
```

*   Ensure `JWT_SECRET_KEY` is a strong, unique key for production.
*   The `DATABASE_URL` is set for SQLite by default. The `instance` folder (for SQLite DB) will be created automatically if it doesn't exist.

## Getting Started

1.  **Navigate to the backend directory:**
    ```bash
    cd platform_backend
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows:
    # venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Option A: Running with Local PostgreSQL (using Docker Compose - Recommended for Development)

This is the recommended way to run the backend locally with a PostgreSQL database, managed by Docker.

1.  **Ensure Docker and Docker Compose are installed.**

2.  **Configure Environment Variables for Docker:**
    *   The `platform_backend/.env` file should be configured with the database credentials that the `docker-compose.yml` file will use for the PostgreSQL service. The defaults in the provided `.env` and `docker-compose.yml` are:
        *   `DB_USER=ghexchangeuser`
        *   `DB_PASSWORD=ghexchangepassword`
        *   `DB_HOST=db` (This is the service name of the PostgreSQL container within the Docker network. If running Flask outside Docker but connecting to Dockerized PG, use `localhost` here.)
        *   `DB_PORT=5432`
        *   `DB_NAME=ghexchange_db`
    *   If you change these in `.env`, ensure they match or are passed correctly in `docker-compose.yml` if it doesn't directly use the .env file for the `db` service's `POSTGRES_` variables. The current `docker-compose.yml` is set up to use these from the `.env` file for the backend service, and has defaults for the db service itself.

3.  **Start PostgreSQL (and Backend service) using Docker Compose:**
    *   In the `platform_backend/` directory, run:
        ```bash
        docker-compose up -d db # Starts only the PostgreSQL database service in detached mode
        ```
    *   Or, to start both the database and the backend service (as defined in `docker-compose.yml`):
        ```bash
        docker-compose up -d # Starts all services in detached mode
        ```
    *   To see logs: `docker-compose logs -f` (for all services) or `docker-compose logs -f db` / `docker-compose logs -f backend`.

4.  **Initialize the database and run migrations (against Dockerized PostgreSQL):**
    *   **If running the Flask app outside Docker** (but DB is in Docker): Ensure your `.env` file has `DB_HOST=localhost` (or your machine's IP if Docker Toolbox on older systems). Then, in your activated local Python virtual environment:
        ```bash
        # First time setup for migrations:
        # flask db init 
        flask db migrate -m "Initial migration for PostgreSQL"
        flask db upgrade
        ```
    *   **If running the Flask app inside Docker via `docker-compose up` (as per the provided `docker-compose.yml`):** You can execute the migration commands inside the running backend container:
        ```bash
        docker-compose exec backend flask db init # Only if 'migrations' folder doesn't exist
        docker-compose exec backend flask db migrate -m "Initial migration for PostgreSQL"
        docker-compose exec backend flask db upgrade
        ```
        (For subsequent model changes, run `docker-compose exec backend flask db migrate -m "Description of changes"` and then `docker-compose exec backend flask db upgrade`)

5.  **Accessing the Application:**
    *   If running the Flask app locally (Option A with only DB in Docker): `http://localhost:5000` (or as configured).
    *   If running the Flask app via `docker-compose up` (Option B): `http://localhost:5000` (as per `docker-compose.yml` port mapping).

### Option B: Running with Local Python Virtual Environment and Manual PostgreSQL/SQLite

1.  **Set up your database:**
    *   **PostgreSQL:** Install PostgreSQL locally. Create a user and a database. Update the `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` variables in your `.env` file accordingly.
    *   **SQLite (Fallback):** If PostgreSQL variables are not set in `.env`, the application will default to SQLite in an `instance/ghexchange_fallback.db` file.

2.  **Initialize the database and run migrations (Local venv):**
    *   Ensure your Python virtual environment is activated.
    *   If this is the first time or if the `migrations` folder doesn't exist:
        ```bash
        flask db init
        # (You only need to run `flask db init` once for the entire project)
        # If you get an error "Error: Failed to find Flask application or factory..."
        # ensure FLASK_APP=run.py is set in your .env file or exported in your shell.
        ```
    *   Create an initial migration (if models have been added/changed and no migration exists):
        ```bash
        flask db migrate -m "Initial migration with User, Product, Order, Trade models"
        ```
    *   Apply the migrations to the database:
        ```bash
        flask db upgrade
        ```
    *   (For subsequent model changes, run `flask db migrate -m "Description of changes"` and then `flask db upgrade`)

3.  **Run the development server (Local venv):**
    ```bash
    flask run
    ```
    This will start the Flask development server, typically on `http://localhost:5000`.


## Cloud Deployment

For deploying this backend to a cloud environment (e.g., AWS, Google Cloud, Heroku, Azure):

1.  **Database:**
    *   It is highly recommended to use a managed PostgreSQL service from your cloud provider (e.g., AWS RDS for PostgreSQL, Google Cloud SQL for PostgreSQL, Heroku Postgres).
    *   Provision a new PostgreSQL instance on your chosen cloud platform.
    *   Obtain the connection credentials (user, password, host, port, database name).

2.  **Environment Variables:**
    *   Set the following environment variables in your cloud application's runtime environment:
        *   `FLASK_APP=run.py`
        *   `FLASK_ENV=production`
        *   `DEBUG=False`
        *   `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` (pointing to your managed PostgreSQL instance).
        *   `JWT_SECRET_KEY` (a strong, unique secret key).
        *   `PYTHONUNBUFFERED=1` (often recommended for Docker/containerized environments for logging).
    *   Alternatively, if your cloud provider or deployment method uses a single `DATABASE_URL` string (e.g., Heroku), ensure your `app/__init__.py` can parse it, or set the individual `DB_*` variables based on it. The current setup in `app/__init__.py` favors individual `DB_*` variables.

3.  **Migrations:**
    *   You will need a strategy to run database migrations in your cloud environment during deployment. Common methods include:
        *   Running `flask db upgrade` as a step in your CI/CD pipeline after deploying new code.
        *   Connecting to a "release" instance or using a one-off task runner provided by your cloud platform to execute the migration command.
        *   Ensure your deployment role/user has permissions to alter the database schema.

4.  **WSGI Server:**
    *   The Flask development server (`flask run`) is not suitable for production. Use a production-grade WSGI server like Gunicorn or uWSGI.
    *   Example Gunicorn command (you might include this in a `Procfile` or your container's CMD):
        ```bash
        gunicorn --workers 3 --bind 0.0.0.0:$PORT run:app 
        # $PORT is often provided by the cloud environment.
        ```

5.  **CORS Configuration:**
    *   In `app/__init__.py`, update the `CORS` origins list to include your production frontend URL(s) instead of just `localhost` development URLs.
        ```python
        # Example for production:
        # CORS(app, resources={r"/api/*": {"origins": ["https://yourfrontenddomain.com"]}})
        ```

## Running Tests

The backend includes a suite of unit and integration tests using `pytest`.

1.  **Ensure your virtual environment is activated** (if not using Docker for tests) and all development dependencies, including testing libraries, are installed:
    ```bash
    pip install -r requirements.txt 
    # This file now includes pytest, pytest-flask, Faker
    ```

2.  **Configure Test Environment (if needed):**
    *   The tests are configured in `tests/conftest.py` to use an **in-memory SQLite database** by default for speed and simplicity, overriding the PostgreSQL configuration during tests. No separate database setup is needed just for running these tests.
    *   If you wish to test against a PostgreSQL database, you would need to modify `tests/conftest.py` and ensure the test PostgreSQL database URL is correctly configured (e.g., via environment variables).

3.  **Run tests using pytest:**
    *   Navigate to the `platform_backend/` directory (the root of the backend project).
    *   Execute the following command:
        ```bash
        pytest
        ```
    *   To run tests with more verbosity:
        ```bash
        pytest -v
        ```
    *   To run a specific test file:
        ```bash
        pytest tests/test_auth_api.py
        ```
    *   To run a specific test function using `-k` keyword expression:
        ```bash
        pytest -k "test_create_product_success"
        ```

## API Structure

*   Authentication: `/api/auth/` (register, login)
*   User Profile: `/api/user/`
*   Hydrogen Products: `/api/products/`
*   Orders: `/api/orders/`
*   Trades: `/api/trades/`

## CORS (Cross-Origin Resource Sharing)

CORS is enabled in `app/__init__.py` to allow requests from typical frontend development server URLs (`http://localhost:3000` and `http://localhost:5173`). If your frontend runs on a different port, you may need to adjust the `origins` list in the CORS configuration.

---

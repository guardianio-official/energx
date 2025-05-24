import pytest
from app.models import User
from faker import Faker

fake = Faker()

def test_register_user_success(client, init_database):
    """Test successful user registration."""
    user_data = {
        'username': fake.user_name(),
        'email': fake.email(),
        'password': 'securepassword123',
        'organization_name': fake.company()
    }
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 201
    assert 'access_token' in response.json
    assert response.json['user']['username'] == user_data['username']
    assert response.json['user']['email'] == user_data['email']

    # Verify user is in DB
    user_in_db = User.query.filter_by(email=user_data['email']).first()
    assert user_in_db is not None
    assert user_in_db.username == user_data['username']

def test_register_user_missing_fields(client, init_database):
    """Test registration with missing fields."""
    response = client.post('/api/auth/register', json={
        'username': fake.user_name(),
        # email is missing
        'password': 'password123'
    })
    assert response.status_code == 400
    assert 'Missing username, email, or password' in response.json['msg']

def test_register_user_duplicate_username(client, new_user):
    """Test registration with a duplicate username."""
    existing_user, _ = new_user # from conftest
    response = client.post('/api/auth/register', json={
        'username': existing_user.username, # Duplicate username
        'email': fake.email(),
        'password': 'newpassword123'
    })
    assert response.status_code == 409
    assert 'Username already exists' in response.json['msg']

def test_register_user_duplicate_email(client, new_user):
    """Test registration with a duplicate email."""
    existing_user, _ = new_user
    response = client.post('/api/auth/register', json={
        'username': fake.user_name(),
        'email': existing_user.email, # Duplicate email
        'password': 'newpassword123'
    })
    assert response.status_code == 409
    assert 'Email already exists' in response.json['msg']

def test_login_user_success_with_email(client, new_user):
    """Test successful user login with email."""
    user, plain_password = new_user
    response = client.post('/api/auth/login', json={
        'identifier': user.email,
        'password': plain_password
    })
    assert response.status_code == 200
    assert 'access_token' in response.json
    assert response.json['user']['username'] == user.username

def test_login_user_success_with_username(client, new_user):
    """Test successful user login with username."""
    user, plain_password = new_user
    response = client.post('/api/auth/login', json={
        'identifier': user.username,
        'password': plain_password
    })
    assert response.status_code == 200
    assert 'access_token' in response.json
    assert response.json['user']['username'] == user.username


def test_login_user_wrong_password(client, new_user):
    """Test login with an incorrect password."""
    user, _ = new_user
    response = client.post('/api/auth/login', json={
        'identifier': user.email,
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    assert 'Bad username/email or password' in response.json['msg']

def test_login_user_nonexistent(client, init_database):
    """Test login for a user that does not exist."""
    response = client.post('/api/auth/login', json={
        'identifier': 'nonexistent@example.com',
        'password': 'password'
    })
    assert response.status_code == 401 # Or 404 depending on desired behavior, 401 is common for login
    assert 'Bad username/email or password' in response.json['msg']


def test_access_protected_route_with_token(client, new_user_with_token):
    """Test accessing a protected route with a valid token."""
    _, token, _ = new_user_with_token
    response = client.get('/api/user/profile', headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 200
    assert 'user' in response.json
    assert response.json['user']['username'] is not None


def test_access_protected_route_without_token(client, init_database):
    """Test accessing a protected route without a token."""
    response = client.get('/api/user/profile')
    assert response.status_code == 401 # Expecting JWT error for missing token
    assert 'Missing Authorization Header' in response.json.get('msg', '') or \
           'Authorization Required' in response.json.get('msg', '')


def test_access_protected_route_with_invalid_token(client, init_database):
    """Test accessing a protected route with an invalid/expired token."""
    response = client.get('/api/user/profile', headers={
        'Authorization': 'Bearer invalidtoken123'
    })
    assert response.status_code == 422 # Expecting JWT error for invalid token format/signature
    assert response.json.get('msg', '').lower().startswith('invalid token') or \
           'not enough segments' in response.json.get('msg','').lower() or \
           'signature verification failed' in response.json.get('msg','').lower()

def test_admin_route_access_by_admin(client, init_database):
    """Test admin route access by an admin user."""
    # Create an admin user
    admin_data = {
        'username': 'test_admin',
        'email': 'admin@example.com',
        'password': 'adminpassword',
        'roles': 'admin,user'
    }
    # Register admin
    reg_response = client.post('/api/auth/register', json=admin_data)
    assert reg_response.status_code == 201
    admin_token = reg_response.json['access_token']

    response = client.get('/api/user/admin/data', headers={
        'Authorization': f'Bearer {admin_token}'
    })
    assert response.status_code == 200
    assert 'This is sensitive admin data' in response.json['data']

def test_admin_route_access_by_non_admin(client, new_user_with_token):
    """Test admin route access denied for non-admin user."""
    _, non_admin_token, _ = new_user_with_token # Regular user
    response = client.get('/api/user/admin/data', headers={
        'Authorization': f'Bearer {non_admin_token}'
    })
    assert response.status_code == 403
    assert 'Admins only!' in response.json['msg']

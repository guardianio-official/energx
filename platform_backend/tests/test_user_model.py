from app.models import User
from faker import Faker

fake = Faker()

def test_new_user_password_hashing(new_user):
    """
    Test that a new user's password is properly hashed and can be checked.
    Uses the 'new_user' fixture from conftest.py which provides (user_object, plain_password).
    """
    user, plain_password = new_user
    assert user.password_hash is not None
    assert user.password_hash != plain_password
    assert user.check_password(plain_password)
    assert not user.check_password(fake.password()) # Check against a random wrong password

def test_user_representation(new_user):
    """Test the __repr__ method of the User model."""
    user, _ = new_user
    assert repr(user) == f'<User {user.username}>'

def test_user_to_dict(new_user):
    """Test the to_dict method of the User model."""
    user, _ = new_user
    user_dict = user.to_dict()

    assert user_dict['id'] == user.id
    assert user_dict['username'] == user.username
    assert user_dict['email'] == user.email
    assert 'password_hash' not in user_dict # Ensure sensitive data is not included
    assert user_dict['organization_name'] == user.organization_name
    assert user_dict['roles'] == (user.roles.split(',') if user.roles else [])
    assert user_dict['created_at'] is not None
    assert user_dict['updated_at'] is not None

def test_user_unique_username_and_email(init_database):
    """Test uniqueness constraints for username and email."""
    db = init_database # Get the db instance
    
    user1_data = {
        'username': 'testuser_unique',
        'email': 'testunique@example.com',
        'password': 'password123'
    }
    user1 = User(**user1_data)
    db.session.add(user1)
    db.session.commit()

    # Attempt to create another user with the same username
    user2_data_same_username = {
        'username': 'testuser_unique', # Same username
        'email': 'anotheremail@example.com',
        'password': 'password123'
    }
    user2 = User(**user2_data_same_username)
    db.session.add(user2)
    try:
        db.session.commit()
        assert False, "Should have raised IntegrityError for duplicate username"
    except Exception as e: # Broad exception to catch backend-specific integrity errors
        db.session.rollback()
        assert "UNIQUE constraint failed" in str(e) or "duplicate key value violates unique constraint" in str(e).lower()


    # Attempt to create another user with the same email
    user3_data_same_email = {
        'username': 'anotheruser',
        'email': 'testunique@example.com', # Same email
        'password': 'password123'
    }
    user3 = User(**user3_data_same_email)
    db.session.add(user3)
    try:
        db.session.commit()
        assert False, "Should have raised IntegrityError for duplicate email"
    except Exception as e:
        db.session.rollback()
        assert "UNIQUE constraint failed" in str(e) or "duplicate key value violates unique constraint" in str(e).lower()


def test_user_roles_default(init_database):
    db = init_database
    user = User(username="roleuser", email="role@example.com", password="password")
    db.session.add(user)
    db.session.commit()
    assert user.roles == "user" # Default role

def test_user_roles_custom(init_database):
    db = init_database
    user = User(username="customroleuser", email="customrole@example.com", password="password", roles="admin,editor")
    db.session.add(user)
    db.session.commit()
    assert user.roles == "admin,editor"
    user_dict = user.to_dict()
    assert "admin" in user_dict['roles']
    assert "editor" in user_dict['roles']

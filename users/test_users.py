import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture(scope='module')
def new_user():
    """Fixture to provide a new user entry."""
    return {
        'username': 'testuser',
        'hashed_password': generate_password_hash('testpassword'),  # Hashed password for testing
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'testuser@example.com',
        'role': 'staff',
        'status': 'active'
    }


def test_create_user(test_client):
    """
    Test case for creating a new user.
    Verifies if the user is successfully created and returns a 201 status code.
    """
    # Clear out any existing user to avoid conflicts
    existing_user = test_client.get('/api/users/1')
    if existing_user.status_code == 200:
        # Remove user if exists
        test_client.delete('/api/users/1')

    new_user = {
        'username': 'newuser',
        'password': 'password',
        'first_name': 'New',
        'last_name': 'User',
        'email': 'newuser@example.com',
        'role': 'staff',
        'status': 'active'
    }
    print("Creating new user with data:", new_user)
    response = test_client.post('/api/users/', json=new_user)
    print(f"Response Status Code: {response.status_code}")
    response_data = response.json
    print(f"Response Data: {response_data}")

    if response.status_code == 400:
        # Check for validation errors
        if 'username' in response_data:
            print(f"Username Validation Error: {response_data['username']}")
        if 'password' in response_data:
            print(f"Password Validation Error: {response_data['password']}")
        if 'email' in response_data:
            print(f"Email Validation Error: {response_data['email']}")

    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    assert 'id' in response_data
    assert response_data['username'] == new_user['username']
    assert response_data['email'] == new_user['email']

def test_get_user(test_client):
    """
    Test case for fetching a user entry by ID.
    Verifies if the response returns the correct user entry with a 200 status code.
    """
    # Check current users in the database for debugging
    response_all = test_client.get('/api/users/')
    print("All Users in the System:", response_all.json)

    # Remove existing user with username
    for user in response_all.json:
        if user['username'] == 'newuser' or user['email'] == 'newuser@example.com':
            delete_response = test_client.delete(f"/api/users/{user['id']}")
            print(f"Deleted existing user: {delete_response.status_code}")

    # Create user with unique data
    user_setup = {
        'username': 'newuser',
        'password': 'password',
        'first_name': 'New',
        'last_name': 'User',
        'email': 'newuser@example.com',
        'role': 'staff',
        'status': 'active'
    }
    create_response = test_client.post('/api/users/', json=user_setup)
    print(f"User Creation Response: {create_response.json}")

    # Verify user was created successfully
    assert create_response.status_code == 201, f"User creation failed: {create_response.json}"

    # Get the newly created user's ID from the response
    new_user_id = create_response.json['id']

    # Now test the user retrieval using the correct ID
    response = test_client.get(f'/api/users/{new_user_id}')
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Data: {response.json}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    response_data = response.json
    assert 'username' in response_data
    assert response_data['username'] == 'newuser'

def test_create_invalid_user(test_client):
    """
    Test case for creating a user with invalid data.
    Verifies if the API returns a 400 status code for invalid input.
    """
    invalid_user = {
        'username': '',  # Invalid (empty)
        'hashed_password': '',  # Invalid (empty)
        'email': 'invalid-email',  # Invalid email format
    }
    response = test_client.post('/api/users/', json=invalid_user)
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    response_data = response.json
    assert 'username' in response_data
    assert 'hashed_password' in response_data
    assert 'email' in response_data

def test_get_nonexistent_user(test_client):
    """
    Test case for fetching a user entry by a non-existent ID.
    Verifies if the response returns a 404 status code.
    """
    response = test_client.get('/api/users/9999')
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    response_data = response.json
    assert 'message' in response_data
    assert response_data['message'] == 'User not found'

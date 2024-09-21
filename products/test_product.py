import pytest
from inventory_system import db

@pytest.fixture
def new_product():
    """
    Fixture for creating a new product test data.
    Returns a dictionary with product details.
    """
    return {
        'name': 'Test Product',
        'description': 'This is a test product',
        'price': '10.99'
    }

def test_create_product(test_client):
    """
    Test case for creating a new product entry.
    Verifies if the product entry is successfully created and returns a 201 status code.
    """
    new_product = {
        'name': 'New Product',
        'description': 'This is a test product.',
        'price': 15.75
    }
    response = test_client.post('/api/products/', json=new_product)
    assert response.status_code == 201
    assert response.json['name'] == 'New Product'
    assert response.json['price'] == '15.75'

def test_get_products(test_client):
    """
    Test case for fetching all products.
    Verifies if the response returns a list of products with a 200 status code.
    """
    # Rollback any pending transactions before running this test
    db.session.rollback()

    response = test_client.get('/api/products/')
    assert response.status_code == 200


def test_create_invalid_product(test_client):
    """
    Test case for creating a product with invalid data.
    Verifies if the API returns a 400 status code for invalid input.
    """
    invalid_product = {"name": "", "price": None}  # Invalid data
    response = test_client.post('/api/products/', json=invalid_product)
    assert response.status_code == 400
    # Rollback after failed transaction
    db.session.rollback()
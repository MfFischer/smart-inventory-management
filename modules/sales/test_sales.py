import pytest


@pytest.fixture(scope='module')
def new_sale():
    """Fixture to provide a new sale entry."""
    return {
        'product_id': 1,
        'quantity': 5,
        'total_price': '100.00',
        'sale_status': 'completed'
    }

def test_create_sale(test_client, new_sale):
    """
    Test case for creating a new sale entry.
    Verifies if the sale entry is successfully created and returns a 201 status code.
    """
    response = test_client.post('/api/sales/', json=new_sale)
    assert response.status_code == 201

def test_get_sales(test_client):
    """
    Test case for fetching all sale entries.
    Verifies if the response returns a list of sales entries with a 200 status code.
    """
    response = test_client.get('/api/sales/')
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) > 0

def test_get_sale(test_client):
    """
    Test case for fetching a sale entry by ID.
    Verifies if the response returns the correct sale entry with a 200 status code.
    """
    response = test_client.get('/api/sales/1')
    assert response.status_code == 200
    assert 'product_id' in response.json
    assert response.json['product_id'] == 1

import pytest

@pytest.fixture
def new_inventory_item():
    """
    Fixture for creating a new inventory item data for testing.
    """
    return {
        "product_id": 1,
        "supplier_id": 1,
        "sku": "SKU004",
        "stock_quantity": 100,
        "reorder_threshold": 10,
        "unit_price": 9.99
    }

def test_create_inventory_item(test_client, new_inventory_item):
    """
    Test case for creating a new inventory item.
    Verifies if the inventory item is successfully created and returns a 201 status code.
    """
    # Use a unique SKU for each test run
    new_inventory_item['sku'] = 'UNIQUE001'
    response = test_client.post('/api/inventory/', json=new_inventory_item)
    assert response.status_code == 201  #

def test_get_inventory(test_client):
    """
    Test case for fetching all inventory items.
    Verifies if the response returns a list of inventory items with a 200 status code.
    """
    response = test_client.get('/api/inventory/')
    assert response.status_code == 200
    # Verify that the response is a list
    assert isinstance(response.get_json(), list)

def test_create_invalid_inventory_item(test_client):
    """
    Test case for creating an inventory item with invalid data.
    Verifies if the API returns a 400 status code for invalid input.
    """
    invalid_inventory = {"product_id": 9999, "stock_quantity": -5}
    response = test_client.post('/api/inventory/', json=invalid_inventory)
    assert response.status_code == 400

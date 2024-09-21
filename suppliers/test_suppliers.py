import pytest
import time


@pytest.fixture(scope='module')
def new_supplier():
    """Fixture to provide a new supplier entry."""
    return {
        'name': 'Test Supplier',
        'email': 'testsupplier@example.com',
        'phone': '1234567890',
        'address': '123 Test Street, Test City, TX'
    }

def test_create_supplier(test_client, new_supplier):
    """
    Test case for creating a new supplier.
    Verifies if the supplier is successfully created and returns a 201 status code.
    """
    response = test_client.post('/api/suppliers/', json=new_supplier)
    assert response.status_code == 201
    response_data = response.json
    assert 'id' in response_data
    assert response_data['name'] == new_supplier['name']
    assert response_data['email'] == new_supplier['email']

def test_create_invalid_supplier(test_client):
    """
    Test case for creating a supplier with invalid data.
    Verifies if the API returns a 400 status code for invalid input.
    """
    invalid_supplier = {
        'name': '',  # Invalid name (empty)
        'email': 'invalid-email'
    }
    response = test_client.post('/api/suppliers/', json=invalid_supplier)
    assert response.status_code == 400
    assert b'Supplier name must not be empty' in response.data
    assert b'Not a valid email address' in response.data

def test_get_suppliers(test_client):
    """
    Test case for fetching all supplier entries.
    Verifies if the response returns a list of supplier entries with a 200 status code.
    """
    response = test_client.get('/api/suppliers/')
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) > 0

def test_get_supplier(test_client, new_supplier):
    """
    Test case for fetching a supplier entry by ID.
    Verifies if the response returns the correct supplier entry with a 200 status code.
    """
    # Remove existing supplier with the same email to avoid conflicts
    existing_suppliers = test_client.get('/api/suppliers/')
    for supplier in existing_suppliers.json:
        if supplier['email'] == new_supplier['email']:
            delete_response = test_client.delete(f"/api/suppliers/{supplier['id']}")
            print(f"Deleted existing supplier with ID {supplier['id']}: {delete_response.status_code}")

    # Create a new supplier
    response = test_client.post('/api/suppliers/', json=new_supplier)
    print(f"Supplier Creation Response Status Code: {response.status_code}")
    print(f"Supplier Creation Response Data: {response.json}")

    # Check if the supplier was created successfully
    assert response.status_code == 201, f"Failed to create supplier: {response.json}"

    # Retrieve the supplier ID
    supplier_id = response.json.get('id')
    assert supplier_id is not None, "Supplier creation did not return an 'id'."

    # Fetch the newly created supplier
    response = test_client.get(f'/api/suppliers/{supplier_id}')
    print(f"Get Supplier Response Status Code: {response.status_code}")
    print(f"Get Supplier Response Data: {response.json}")

    assert response.status_code == 200
    assert 'name' in response.json
    assert response.json['name'] == new_supplier['name']


def test_get_nonexistent_supplier(test_client):
    """
    Test case for fetching a supplier entry that does not exist.
    Verifies if the API returns a 404 status code.
    """
    # Print the allowed methods for the route (for debugging)
    response_options = test_client.options('/api/suppliers/9999')
    print(f"Allowed Methods for /api/suppliers/9999: {response_options.headers.get('Allow')}")

    response = test_client.get('/api/suppliers/9999')
    print(f"Non-existent Supplier Response Status Code: {response.status_code}")
    print(f"Non-existent Supplier Response Data: {response.json}")

    assert response.status_code == 404, f"Expected 404, got {response.status_code}"


def test_update_supplier(test_client):
    """
    Test case for updating an existing supplier.
    Verifies if the supplier entry is successfully updated and returns a 200 status code.
    """
    # Use a unique email to avoid conflicts
    unique_email = f"testsupplier{int(time.time())}@example.com"
    new_supplier = {
        'address': '123 Test Street, Test City, TX',
        'email': unique_email,
        'name': 'Test Supplier',
        'phone': '1234567890'
    }

    # Create a new supplier
    response = test_client.post('/api/suppliers/', json=new_supplier)
    print(f"Supplier Creation Response Status Code: {response.status_code}")
    print(f"Supplier Creation Response Data: {response.json}")

    # Check if the supplier was created successfully
    assert response.status_code == 201, f"Failed to create supplier: {response.json}"

    # Retrieve the supplier ID
    supplier_id = response.json.get('id')
    assert supplier_id is not None, "Supplier creation did not return an 'id'."

    # Update the supplier
    updated_supplier = {
        'name': 'Updated Supplier',
        'email': f"updated{unique_email}"
    }
    response = test_client.put(f'/api/suppliers/{supplier_id}', json=updated_supplier)
    print(f"Update Supplier Response Status Code: {response.status_code}")
    print(f"Update Supplier Response Data: {response.json}")

    assert response.status_code == 200
    assert response.json['name'] == updated_supplier['name']
    assert response.json['email'] == updated_supplier['email']


def test_delete_supplier(test_client, new_supplier):
    """
    Test case for deleting a supplier entry.
    Verifies if the supplier entry is successfully deleted and returns a 204 status code.
    """
    # Remove existing supplier with the same email to avoid conflicts
    existing_suppliers = test_client.get('/api/suppliers/')
    for supplier in existing_suppliers.json:
        if supplier['email'] == new_supplier['email']:
            delete_response = test_client.delete(f"/api/suppliers/{supplier['id']}")
            print(f"Deleted existing supplier with ID {supplier['id']}: {delete_response.status_code}")

    # Create a new supplier
    response = test_client.post('/api/suppliers/', json=new_supplier)
    print(f"Supplier Creation Response Status Code: {response.status_code}")
    print(f"Supplier Creation Response Data: {response.json}")

    # Check if the supplier was created successfully
    assert response.status_code == 201, f"Failed to create supplier: {response.json}"

    # Retrieve the supplier ID
    supplier_id = response.json.get('id')
    assert supplier_id is not None, "Supplier creation did not return an 'id'."

    # Delete the supplier
    response = test_client.delete(f'/api/suppliers/{supplier_id}')
    print(f"Delete Supplier Response Status Code: {response.status_code}")
    assert response.status_code == 204

    # Verify the supplier is deleted
    response = test_client.get(f'/api/suppliers/{supplier_id}')
    print(f"Get Deleted Supplier Response Status Code: {response.status_code}")
    assert response.status_code == 404
    assert b'Supplier not found' in response.data


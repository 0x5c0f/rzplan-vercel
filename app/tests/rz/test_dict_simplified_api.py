"""Tests for simplified dictionary API endpoints"""
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.rz.crud import dict_crud
from app.rz.models.dict_type import DictTypeCreate


def test_create_dict_item_by_code(client: TestClient, db: Session) -> None:
    """Test creating a dictionary item using type_code (simplified API)"""
    # Create a dict type first
    type_code = f"test_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test Type",
        description="Test description",
    )
    dict_type = dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    # Create dict item using simplified API
    item_data = {
        "item_code": "test_item",
        "item_value": "Test Value",
        "sort_order": 1,
    }
    response = client.post(
        f"{settings.API_V1_STR}/dict/{type_code}/items",
        json=item_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["item_code"] == "test_item"
    assert content["item_value"] == "Test Value"
    assert content["sort_order"] == 1
    assert content["type_id"] == str(dict_type.id)


def test_list_dict_items_by_code(client: TestClient, db: Session) -> None:
    """Test listing dictionary items using type_code (simplified API)"""
    # Create a dict type and items
    type_code = f"test_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test Type",
        description="Test description",
    )
    dict_type = dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    # Create items using simplified API
    for i in range(3):
        item_data = {
            "item_code": f"item_{i}",
            "item_value": f"Value {i}",
            "sort_order": i,
        }
        client.post(
            f"{settings.API_V1_STR}/dict/{type_code}/items",
            json=item_data,
        )
    
    # List items using simplified API
    response = client.get(f"{settings.API_V1_STR}/dict/{type_code}/items")
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 3
    assert len(content["data"]) == 3


def test_get_dict_item_by_code(client: TestClient, db: Session) -> None:
    """Test getting a dictionary item using type_code and item_code (simplified API)"""
    # Create a dict type and item
    type_code = f"test_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test Type",
        description="Test description",
    )
    dict_type = dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    item_data = {
        "item_code": "test_item",
        "item_value": "Test Value",
    }
    client.post(
        f"{settings.API_V1_STR}/dict/{type_code}/items",
        json=item_data,
    )
    
    # Get item using simplified API
    response = client.get(
        f"{settings.API_V1_STR}/dict/{type_code}/items/test_item"
    )
    assert response.status_code == 200
    content = response.json()
    assert content["item_code"] == "test_item"
    assert content["item_value"] == "Test Value"


def test_update_dict_item_by_code(client: TestClient, db: Session) -> None:
    """Test updating a dictionary item using type_code and item_code (simplified API)"""
    # Create a dict type and item
    type_code = f"test_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test Type",
        description="Test description",
    )
    dict_type = dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    item_data = {
        "item_code": "test_item",
        "item_value": "Original Value",
    }
    client.post(
        f"{settings.API_V1_STR}/dict/{type_code}/items",
        json=item_data,
    )
    
    # Update item using simplified API
    update_data = {
        "item_value": "Updated Value",
        "sort_order": 10,
    }
    response = client.put(
        f"{settings.API_V1_STR}/dict/{type_code}/items/test_item",
        json=update_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["item_value"] == "Updated Value"
    assert content["sort_order"] == 10


def test_delete_dict_item_by_code(client: TestClient, db: Session) -> None:
    """Test deleting a dictionary item using type_code and item_code (simplified API)"""
    # Create a dict type and item
    type_code = f"test_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test Type",
        description="Test description",
    )
    dict_type = dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    item_data = {
        "item_code": "test_item",
        "item_value": "Test Value",
    }
    client.post(
        f"{settings.API_V1_STR}/dict/{type_code}/items",
        json=item_data,
    )
    
    # Delete item using simplified API
    response = client.delete(
        f"{settings.API_V1_STR}/dict/{type_code}/items/test_item"
    )
    assert response.status_code == 200
    
    # Verify item is deleted (soft delete)
    response = client.get(
        f"{settings.API_V1_STR}/dict/{type_code}/items/test_item"
    )
    assert response.status_code == 404


def test_create_dict_item_by_code_type_not_found(client: TestClient) -> None:
    """Test creating a dictionary item with non-existent type_code"""
    item_data = {
        "item_code": "test_item",
        "item_value": "Test Value",
    }
    response = client.post(
        f"{settings.API_V1_STR}/dict/nonexistent_type/items",
        json=item_data,
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_dict_item_by_code_duplicate(client: TestClient, db: Session) -> None:
    """Test creating a duplicate dictionary item using simplified API"""
    # Create a dict type and item
    type_code = f"test_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test Type",
        description="Test description",
    )
    dict_type = dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    item_data = {
        "item_code": "test_item",
        "item_value": "Test Value",
    }
    # Create first item
    response = client.post(
        f"{settings.API_V1_STR}/dict/{type_code}/items",
        json=item_data,
    )
    assert response.status_code == 200
    
    # Try to create duplicate
    response = client.post(
        f"{settings.API_V1_STR}/dict/{type_code}/items",
        json=item_data,
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_get_dict_item_by_code_not_found(client: TestClient, db: Session) -> None:
    """Test getting a non-existent dictionary item using simplified API"""
    # Create a dict type
    type_code = f"test_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test Type",
        description="Test description",
    )
    dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    # Try to get non-existent item
    response = client.get(
        f"{settings.API_V1_STR}/dict/{type_code}/items/nonexistent_item"
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_dict_item_by_code_not_found(client: TestClient, db: Session) -> None:
    """Test updating a non-existent dictionary item using simplified API"""
    # Create a dict type
    type_code = f"test_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test Type",
        description="Test description",
    )
    dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    # Try to update non-existent item
    update_data = {
        "item_value": "Updated Value",
    }
    response = client.put(
        f"{settings.API_V1_STR}/dict/{type_code}/items/nonexistent_item",
        json=update_data,
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_dict_item_by_code_not_found(client: TestClient, db: Session) -> None:
    """Test deleting a non-existent dictionary item using simplified API"""
    # Create a dict type
    type_code = f"test_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test Type",
        description="Test description",
    )
    dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    # Try to delete non-existent item
    response = client.delete(
        f"{settings.API_V1_STR}/dict/{type_code}/items/nonexistent_item"
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

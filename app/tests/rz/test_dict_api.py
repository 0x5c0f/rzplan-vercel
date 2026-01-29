"""Tests for dictionary API endpoints"""
import uuid
from fastapi.testclient import TestClient

from app.core.config import settings


def test_create_dict_type(client: TestClient) -> None:
    """测试创建字典类型"""
    # Use UUID to ensure uniqueness
    unique_code = f"test_type_{uuid.uuid4().hex[:8]}"
    data = {
        "type_code": unique_code,
        "type_name": "Test Type",
        "description": "Test description",
        "is_enabled": True,
    }
    response = client.post(
        f"{settings.API_V1_STR}/dict/types",
        json=data,
    )
    assert response.status_code == 200, f"Response: {response.json()}"
    content = response.json()
    assert content["type_code"] == data["type_code"]
    assert content["type_name"] == data["type_name"]
    assert "id" in content


def test_list_dict_types(client: TestClient) -> None:
    """测试获取字典类型列表"""
    response = client.get(
        f"{settings.API_V1_STR}/dict/types",
    )
    assert response.status_code == 200
    content = response.json()
    assert isinstance(content, list)


def test_get_dict_type_by_code(client: TestClient) -> None:
    """测试根据代码获取字典类型"""
    # First create a type
    unique_code = f"get_test_type_{uuid.uuid4().hex[:8]}"
    data = {
        "type_code": unique_code,
        "type_name": "Get Test Type",
    }
    create_response = client.post(
        f"{settings.API_V1_STR}/dict/types",
        json=data,
    )
    assert create_response.status_code == 200, f"Response: {create_response.json()}"
    
    # Then get it by code
    response = client.get(
        f"{settings.API_V1_STR}/dict/types/code/{data['type_code']}",
    )
    assert response.status_code == 200
    content = response.json()
    assert content["type_code"] == data["type_code"]


def test_update_dict_type(client: TestClient) -> None:
    """测试更新字典类型"""
    # Create a type first
    unique_code = f"update_test_{uuid.uuid4().hex[:8]}"
    create_data = {
        "type_code": unique_code,
        "type_name": "Original Name",
    }
    create_response = client.post(
        f"{settings.API_V1_STR}/dict/types",
        json=create_data,
    )
    assert create_response.status_code == 200
    type_id = create_response.json()["id"]
    
    # Update it
    update_data = {
        "type_name": "Updated Name",
        "description": "Updated description",
    }
    response = client.put(
        f"{settings.API_V1_STR}/dict/types/{type_id}",
        json=update_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["type_name"] == update_data["type_name"]
    assert content["description"] == update_data["description"]


def test_delete_dict_type(client: TestClient) -> None:
    """测试删除字典类型（软删除）"""
    # Create a type first
    unique_code = f"delete_test_{uuid.uuid4().hex[:8]}"
    create_data = {
        "type_code": unique_code,
        "type_name": "Delete Test",
    }
    create_response = client.post(
        f"{settings.API_V1_STR}/dict/types",
        json=create_data,
    )
    assert create_response.status_code == 200
    type_id = create_response.json()["id"]
    
    # Soft delete it (default)
    response = client.delete(
        f"{settings.API_V1_STR}/dict/types/{type_id}",
    )
    assert response.status_code == 200
    assert "soft deleted" in response.json()["message"]
    
    # Verify it still exists but is_enabled=False (need to query with enabled_only=false)
    get_response = client.get(
        f"{settings.API_V1_STR}/dict/types/{type_id}?enabled_only=false",
    )
    assert get_response.status_code == 200
    content = get_response.json()
    assert content["is_enabled"] == False


def test_create_dict_item(client: TestClient) -> None:
    """测试创建字典项"""
    # Create a type first
    unique_code = f"item_test_type_{uuid.uuid4().hex[:8]}"
    type_data = {
        "type_code": unique_code,
        "type_name": "Item Test Type",
    }
    type_response = client.post(
        f"{settings.API_V1_STR}/dict/types",
        json=type_data,
    )
    assert type_response.status_code == 200
    type_id = type_response.json()["id"]
    
    # Create an item
    item_data = {
        "type_id": type_id,
        "item_code": "test_item",
        "item_value": "Test Value",
        "sort_order": 1,
    }
    response = client.post(
        f"{settings.API_V1_STR}/dict/items",
        json=item_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["item_code"] == item_data["item_code"]
    assert content["item_value"] == item_data["item_value"]
    assert "id" in content


def test_list_dict_items(client: TestClient) -> None:
    """测试获取字典项列表"""
    response = client.get(
        f"{settings.API_V1_STR}/dict/items",
    )
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content
    assert isinstance(content["data"], list)


def test_update_dict_item(client: TestClient) -> None:
    """测试更新字典项"""
    # Create a type and item first
    unique_code = f"update_item_type_{uuid.uuid4().hex[:8]}"
    type_data = {
        "type_code": unique_code,
        "type_name": "Update Item Type",
    }
    type_response = client.post(
        f"{settings.API_V1_STR}/dict/types",
        json=type_data,
    )
    type_id = type_response.json()["id"]
    
    item_data = {
        "type_id": type_id,
        "item_code": "update_item",
        "item_value": "Original Value",
    }
    item_response = client.post(
        f"{settings.API_V1_STR}/dict/items",
        json=item_data,
    )
    item_id = item_response.json()["id"]
    
    # Update the item
    update_data = {
        "item_value": "Updated Value",
        "sort_order": 10,
    }
    response = client.put(
        f"{settings.API_V1_STR}/dict/items/{item_id}",
        json=update_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["item_value"] == update_data["item_value"]
    assert content["sort_order"] == update_data["sort_order"]


def test_delete_dict_item(client: TestClient) -> None:
    """测试删除字典项（软删除）"""
    # Create a type and item first
    unique_code = f"delete_item_type_{uuid.uuid4().hex[:8]}"
    type_data = {
        "type_code": unique_code,
        "type_name": "Delete Item Type",
    }
    type_response = client.post(
        f"{settings.API_V1_STR}/dict/types",
        json=type_data,
    )
    type_id = type_response.json()["id"]
    
    item_data = {
        "type_id": type_id,
        "item_code": "delete_item",
        "item_value": "Delete Value",
    }
    item_response = client.post(
        f"{settings.API_V1_STR}/dict/items",
        json=item_data,
    )
    item_id = item_response.json()["id"]
    
    # Soft delete the item (default)
    response = client.delete(
        f"{settings.API_V1_STR}/dict/items/{item_id}",
    )
    assert response.status_code == 200
    assert "soft deleted" in response.json()["message"]
    
    # Verify it still exists but is_enabled=False
    get_response = client.get(
        f"{settings.API_V1_STR}/dict/items/{item_id}",
    )
    assert get_response.status_code == 200
    content = get_response.json()
    assert content["is_enabled"] == False



def test_delete_dict_type_with_items_no_cascade(client: TestClient) -> None:
    """测试删除有关联项的字典类型（不级联）"""
    # Create a type and item
    unique_code = f"cascade_test_{uuid.uuid4().hex[:8]}"
    type_data = {
        "type_code": unique_code,
        "type_name": "Cascade Test Type",
    }
    type_response = client.post(
        f"{settings.API_V1_STR}/dict/types",
        json=type_data,
    )
    type_id = type_response.json()["id"]
    
    item_data = {
        "type_id": type_id,
        "item_code": "test_item",
        "item_value": "Test Value",
    }
    client.post(
        f"{settings.API_V1_STR}/dict/items",
        json=item_data,
    )
    
    # Try to delete without cascade - should fail
    response = client.delete(
        f"{settings.API_V1_STR}/dict/types/{type_id}",
    )
    assert response.status_code == 400
    assert "associated items" in response.json()["detail"]


def test_delete_dict_type_with_cascade(client: TestClient) -> None:
    """测试级联删除字典类型及其关联项"""
    # Create a type and multiple items
    unique_code = f"cascade_delete_{uuid.uuid4().hex[:8]}"
    type_data = {
        "type_code": unique_code,
        "type_name": "Cascade Delete Type",
    }
    type_response = client.post(
        f"{settings.API_V1_STR}/dict/types",
        json=type_data,
    )
    type_id = type_response.json()["id"]
    
    # Create 3 items
    for i in range(3):
        item_data = {
            "type_id": type_id,
            "item_code": f"item_{i}",
            "item_value": f"Value {i}",
        }
        client.post(
            f"{settings.API_V1_STR}/dict/items",
            json=item_data,
        )
    
    # Delete with cascade
    response = client.delete(
        f"{settings.API_V1_STR}/dict/types/{type_id}?cascade=true",
    )
    assert response.status_code == 200
    assert "3 items" in response.json()["message"]
    
    # Verify type is soft deleted (need to query with enabled_only=false)
    get_type_response = client.get(
        f"{settings.API_V1_STR}/dict/types/{type_id}?enabled_only=false",
    )
    assert get_type_response.status_code == 200
    assert get_type_response.json()["is_enabled"] == False
    
    # Verify items are soft deleted (need to query with enabled_only=false)
    items_response = client.get(
        f"{settings.API_V1_STR}/dict/items?type_id={type_id}&enabled_only=false",
    )
    assert items_response.status_code == 200
    items = items_response.json()["data"]
    assert len(items) == 3
    for item in items:
        assert item["is_enabled"] == False


def test_hard_delete_dict_type(client: TestClient) -> None:
    """测试硬删除字典类型"""
    # Create a type
    unique_code = f"hard_delete_{uuid.uuid4().hex[:8]}"
    create_data = {
        "type_code": unique_code,
        "type_name": "Hard Delete Test",
    }
    create_response = client.post(
        f"{settings.API_V1_STR}/dict/types",
        json=create_data,
    )
    type_id = create_response.json()["id"]
    
    # Hard delete it
    response = client.delete(
        f"{settings.API_V1_STR}/dict/types/{type_id}?hard_delete=true",
    )
    assert response.status_code == 200
    assert "permanently deleted" in response.json()["message"]
    
    # Verify it's really gone
    get_response = client.get(
        f"{settings.API_V1_STR}/dict/types/{type_id}",
    )
    assert get_response.status_code == 404

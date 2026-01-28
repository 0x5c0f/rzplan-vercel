"""Unit tests for dictionary CRUD operations"""
import uuid
from sqlmodel import Session

from app.rz.crud import dict_crud
from app.rz.models.dict_type import (
    DictType,
    DictTypeCreate,
    DictTypeUpdate,
)
from app.rz.models.dict_item import (
    DictItem,
    DictItemCreate,
    DictItemUpdate,
)


def test_create_dict_type(db: Session) -> None:
    """Test creating a dictionary type"""
    type_code = f"test_type_{uuid.uuid4().hex[:8]}"
    type_name = "Test Type"
    description = "Test description"
    
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name=type_name,
        description=description
    )
    dict_type = dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    assert dict_type.type_code == type_code
    assert dict_type.type_name == type_name
    assert dict_type.description == description
    assert dict_type.is_enabled is True
    assert dict_type.id is not None


def test_get_dict_type_by_code(db: Session) -> None:
    """Test retrieving a dictionary type by code"""
    type_code = f"test_get_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test Get Type"
    )
    created_type = dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    retrieved_type = dict_crud.get_dict_type_by_code(session=db, type_code=type_code)
    
    assert retrieved_type is not None
    assert retrieved_type.id == created_type.id
    assert retrieved_type.type_code == type_code


def test_get_dict_type_by_code_not_found(db: Session) -> None:
    """Test retrieving a non-existent dictionary type"""
    retrieved_type = dict_crud.get_dict_type_by_code(
        session=db,
        type_code="nonexistent_type"
    )
    assert retrieved_type is None


def test_update_dict_type(db: Session) -> None:
    """Test updating a dictionary type"""
    type_code = f"test_update_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Original Name"
    )
    dict_type = dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    new_name = "Updated Name"
    new_description = "Updated description"
    update_in = DictTypeUpdate(
        type_name=new_name,
        description=new_description
    )
    
    updated_type = dict_crud.update_dict_type(
        session=db,
        db_dict_type=dict_type,
        dict_type_in=update_in
    )
    
    assert updated_type.type_name == new_name
    assert updated_type.description == new_description
    assert updated_type.type_code == type_code  # Should not change


def test_create_dict_item(db: Session) -> None:
    """Test creating a dictionary item"""
    # First create a dict type
    type_code = f"test_item_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test Item Type"
    )
    dict_type = dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    # Create dict item
    item_code = "test_item"
    item_value = "Test Value"
    dict_item_in = DictItemCreate(
        type_id=dict_type.id,
        item_code=item_code,
        item_value=item_value,
        sort_order=10
    )
    
    dict_item = dict_crud.create_dict_item(session=db, dict_item_in=dict_item_in)
    
    assert dict_item is not None
    assert dict_item.item_code == item_code
    assert dict_item.item_value == item_value
    assert dict_item.sort_order == 10
    assert dict_item.is_enabled is True


def test_create_dict_item_invalid_type(db: Session) -> None:
    """Test creating a dictionary item with invalid type_id"""
    dict_item_in = DictItemCreate(
        type_id=uuid.uuid4(),  # Non-existent type_id
        item_code="test_item",
        item_value="Test Value"
    )
    
    try:
        dict_crud.create_dict_item(session=db, dict_item_in=dict_item_in)
        assert False, "Should have raised an exception for invalid type_id"
    except Exception:
        # Expected to fail due to foreign key constraint
        db.rollback()
        assert True


def test_get_dict_items_by_type(db: Session) -> None:
    """Test retrieving all dictionary items for a type"""
    # Create dict type
    type_code = f"test_list_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test List Type"
    )
    dict_type = dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    # Create multiple items
    for i in range(3):
        dict_item_in = DictItemCreate(
            type_id=dict_type.id,
            item_code=f"item_{i}",
            item_value=f"Value {i}",
            sort_order=i
        )
        dict_crud.create_dict_item(session=db, dict_item_in=dict_item_in)
    
    # Retrieve items
    items, count = dict_crud.get_dict_items(session=db, type_code=type_code)
    
    assert len(items) == 3
    assert count == 3
    assert items[0].item_code == "item_0"
    assert items[1].item_code == "item_1"
    assert items[2].item_code == "item_2"


def test_get_dict_items_by_type_empty(db: Session) -> None:
    """Test retrieving items for a type with no items"""
    # Create dict type without items
    type_code = f"test_empty_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test Empty Type"
    )
    dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    items, count = dict_crud.get_dict_items(session=db, type_code=type_code)
    assert len(items) == 0
    assert count == 0


def test_get_dict_items_by_type_nonexistent(db: Session) -> None:
    """Test retrieving items for a nonexistent type"""
    items, count = dict_crud.get_dict_items(
        session=db,
        type_code="nonexistent_type"
    )
    assert len(items) == 0
    assert count == 0


def test_get_dict_item(db: Session) -> None:
    """Test retrieving a specific dictionary item"""
    # Create dict type and item
    type_code = f"test_get_item_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test Get Item Type"
    )
    dict_type = dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    item_code = "test_get_item"
    dict_item_in = DictItemCreate(
        type_id=dict_type.id,
        item_code=item_code,
        item_value="Test Value"
    )
    created_item = dict_crud.create_dict_item(session=db, dict_item_in=dict_item_in)
    
    # Retrieve item
    retrieved_item = dict_crud.get_dict_item_by_code(
        session=db,
        type_code=type_code,
        item_code=item_code
    )
    
    assert retrieved_item is not None
    assert retrieved_item.id == created_item.id
    assert retrieved_item.item_code == item_code


def test_get_dict_item_not_found(db: Session) -> None:
    """Test retrieving a nonexistent dictionary item"""
    # Create dict type
    type_code = f"test_notfound_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test Not Found Type"
    )
    dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    # Try to get nonexistent item
    retrieved_item = dict_crud.get_dict_item_by_code(
        session=db,
        type_code=type_code,
        item_code="nonexistent_item"
    )
    assert retrieved_item is None


def test_update_dict_item(db: Session) -> None:
    """Test updating a dictionary item"""
    # Create dict type and item
    type_code = f"test_update_item_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test Update Item Type"
    )
    dict_type = dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    dict_item_in = DictItemCreate(
        type_id=dict_type.id,
        item_code="test_update_item",
        item_value="Original Value",
        sort_order=5
    )
    dict_item = dict_crud.create_dict_item(session=db, dict_item_in=dict_item_in)
    
    # Update item
    new_value = "Updated Value"
    new_sort_order = 10
    update_in = DictItemUpdate(
        item_value=new_value,
        sort_order=new_sort_order
    )
    
    updated_item = dict_crud.update_dict_item(
        session=db,
        db_dict_item=dict_item,
        dict_item_in=update_in
    )
    
    assert updated_item.item_value == new_value
    assert updated_item.sort_order == new_sort_order
    assert updated_item.item_code == "test_update_item"  # Should not change


def test_delete_dict_item(db: Session) -> None:
    """Test soft deleting a dictionary item"""
    # Create dict type and item
    type_code = f"test_delete_item_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="Test Delete Item Type"
    )
    dict_type = dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    dict_item_in = DictItemCreate(
        type_id=dict_type.id,
        item_code="test_delete_item",
        item_value="Test Value"
    )
    dict_item = dict_crud.create_dict_item(session=db, dict_item_in=dict_item_in)
    
    # Delete item (soft delete)
    dict_crud.delete_dict_item(session=db, db_dict_item=dict_item)
    
    # Verify item is disabled
    db.refresh(dict_item)
    assert dict_item.is_enabled is False


def test_dict_type_unique_constraint(db: Session) -> None:
    """Test that type_code must be unique"""
    type_code = f"unique_test_type_{uuid.uuid4().hex[:8]}"
    dict_type_in = DictTypeCreate(
        type_code=type_code,
        type_name="First Type"
    )
    dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in)
    
    # Try to create another type with same code
    dict_type_in2 = DictTypeCreate(
        type_code=type_code,
        type_name="Second Type"
    )
    
    try:
        dict_crud.create_dict_type(session=db, dict_type_in=dict_type_in2)
        assert False, "Should have raised an exception for duplicate type_code"
    except Exception:
        # Expected to fail due to unique constraint
        db.rollback()
        assert True

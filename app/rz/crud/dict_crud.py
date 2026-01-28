"""CRUD operations for dictionary tables"""
import uuid

from sqlmodel import Session, select, func

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

from app.rz.utils.utils import get_datetime_utc


# DictType CRUD operations
def get_dict_types(
    *, session: Session, skip: int = 0, limit: int = 100, enabled_only: bool = True
) -> list[DictType]:
    """Get list of dictionary types"""
    statement = select(DictType)
    
    if enabled_only:
        statement = statement.where(DictType.is_enabled == True)
    
    statement = statement.offset(skip).limit(limit)
    return list(session.exec(statement).all())


def get_dict_type(*, session: Session, type_id: uuid.UUID, enabled_only: bool = True) -> DictType | None:
    """Get dictionary type by ID"""
    statement = select(DictType).where(DictType.id == type_id)

    if enabled_only:
        statement = statement.where(DictType.is_enabled == True)
        
    return session.exec(statement).first()


def get_dict_type_by_code(*, session: Session, type_code: str, enabled_only: bool = True) -> DictType | None:
    """Get dictionary type by code"""
    statement = select(DictType).where(DictType.type_code == type_code)
    
    if enabled_only:
        statement = statement.where(DictType.is_enabled == True)
        
    return session.exec(statement).first()


def create_dict_type(*, session: Session, dict_type_in: DictTypeCreate) -> DictType:
    """Create a new dictionary type"""
    db_obj = DictType.model_validate(dict_type_in)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_dict_type(
    *, session: Session, db_dict_type: DictType, dict_type_in: DictTypeUpdate
) -> DictType:
    """Update dictionary type"""
    update_data = dict_type_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = get_datetime_utc()
    db_dict_type.sqlmodel_update(update_data)
    session.add(db_dict_type)
    session.commit()
    session.refresh(db_dict_type)
    return db_dict_type


def delete_dict_type(
    *, session: Session, db_dict_type: DictType, hard_delete: bool = False
) -> None:
    """Delete dictionary type
    
    Args:
        session: Database session
        db_dict_type: DictType object to delete
        hard_delete: If True, permanently delete; if False (default), soft delete (set is_enabled=False)
    """
    if hard_delete:
        session.delete(db_dict_type)
    else:
        # Soft delete: set is_enabled to False
        db_dict_type.is_enabled = False
        db_dict_type.updated_at = get_datetime_utc()
        session.add(db_dict_type)
    session.commit()


def cascade_delete_dict_items(
    *, session: Session, type_id: uuid.UUID, hard_delete: bool = False
) -> int:
    """Cascade delete all items for a dictionary type
    
    Args:
        session: Database session
        type_id: Dictionary type ID
        hard_delete: If True, permanently delete; if False (default), soft delete (set is_enabled=False)
        
    Returns:
        Number of items deleted
    """
    statement = select(DictItem).where(DictItem.type_id == type_id)
    items = session.exec(statement).all()
    
    count = 0
    for item in items:
        if hard_delete:
            session.delete(item)
        else:
            # Soft delete: set is_enabled to False
            item.is_enabled = False
            item.updated_at = get_datetime_utc()
            session.add(item)
        count += 1
    
    session.commit()
    return count


def count_dict_items_by_type(*, session: Session, type_id: uuid.UUID) -> int:
    """Count dictionary items for a specific type"""
    statement = select(func.count()).select_from(DictItem).where(DictItem.type_id == type_id)
    return session.exec(statement).one()


# DictItem CRUD operations
def get_dict_items(
    *,
    session: Session,
    type_id: uuid.UUID | None = None,
    type_code: str | None = None,
    enabled_only: bool = True,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[DictItem], int]:
    """Get list of dictionary items with count
    
    Returns:
        Tuple of (items list, total count)
    """
    statement = select(DictItem)
    
    # Filter by type_id or type_code
    if type_id:
        statement = statement.where(DictItem.type_id == type_id)
    elif type_code:
        # Join with DictType to filter by type_code
        statement = statement.join(DictType).where(DictType.type_code == type_code)
    
    if enabled_only:
        statement = statement.where(DictItem.is_enabled == True)
    
    # Get count
    count_statement = select(func.count()).select_from(statement.subquery())
    count = session.exec(count_statement).one()
    
    # Get items with pagination and ordering
    statement = statement.order_by(DictItem.sort_order, DictItem.created_at).offset(skip).limit(limit)
    items = list(session.exec(statement).all())
    
    return items, count

def get_dict_items_by_type_id(
    *,
    session: Session, 
    type_id: uuid.UUID, 
    enabled_only: bool = True, 
    skip: int = 0, limit: int = 100
) -> tuple[list[DictItem], int]:
    """Get list of dictionary items by type ID with count
    
    Returns:
        Tuple of (items list, total count)
    """
    statement = select(DictItem).where(DictItem.type_id == type_id)
    
    if enabled_only:
        statement = statement.where(DictItem.is_enabled == True)
    
    # Get count
    count_statement = select(func.count()).select_from(statement.subquery())
    count = session.exec(count_statement).one()
    
    # Get items with pagination and ordering
    statement = statement.order_by(DictItem.sort_order, DictItem.created_at).offset(skip).limit(limit)
    items = list(session.exec(statement).all())
    
    return items, count

def get_dict_items_by_type_code(
    *, 
    session: Session, 
    type_code: str, 
    enabled_only: bool = True,
    skip: int = 0, limit: int = 100
) -> tuple[list[DictItem], int]:
    """Get list of dictionary items by type code with count
    
    Returns:
        Tuple of (items list, total count)
    """
    # Join with DictType to filter by type_code
    statement = select(DictItem).join(DictType).where(DictType.type_code == type_code)
    
    if enabled_only:
        statement = statement.where(DictItem.is_enabled == True)
    
    # Get count
    count_statement = select(func.count()).select_from(statement.subquery())
    count = session.exec(count_statement).one()
    
    # Get items with pagination and ordering
    statement = statement.order_by(DictItem.sort_order, DictItem.created_at).offset(skip).limit(limit)
    items = list(session.exec(statement).all())
    
    return items, count

def get_dict_item(*, session: Session, item_id: uuid.UUID) -> DictItem | None:
    """Get dictionary item by ID"""
    statement = select(DictItem).where(DictItem.id == item_id)
    return session.exec(statement).first()


def get_dict_item_by_code(
    *, session: Session, type_code: str, item_code: str
) -> DictItem | None:
    """Get a specific dictionary item by type_code and item_code"""
    dict_type = get_dict_type_by_code(session=session, type_code=type_code)
    if not dict_type:
        return None
    
    statement = select(DictItem).where(
        DictItem.type_id == dict_type.id,
        DictItem.item_code == item_code
    )
    return session.exec(statement).first()


def create_dict_item(*, session: Session, dict_item_in: DictItemCreate) -> DictItem:
    """Create a new dictionary item"""
    db_obj = DictItem.model_validate(dict_item_in)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_dict_item(
    *, session: Session, db_dict_item: DictItem, dict_item_in: DictItemUpdate
) -> DictItem:
    """Update dictionary item"""
    update_data = dict_item_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = get_datetime_utc()
    db_dict_item.sqlmodel_update(update_data)
    session.add(db_dict_item)
    session.commit()
    session.refresh(db_dict_item)
    return db_dict_item


def delete_dict_item(
    *, session: Session, db_dict_item: DictItem, hard_delete: bool = False
) -> None:
    """Delete dictionary item
    
    Args:
        session: Database session
        db_dict_item: DictItem object to delete
        hard_delete: If True, permanently delete; if False (default), soft delete (set is_enabled=False)
    """
    if hard_delete:
        session.delete(db_dict_item)
    else:
        # Soft delete: set is_enabled to False
        db_dict_item.is_enabled = False
        db_dict_item.updated_at = get_datetime_utc()
        session.add(db_dict_item)
    session.commit()

"""Dictionary API routes"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import SessionDep
from app.models import Message
from app.rz.models.dict_type import (
    DictTypePublic,
    DictTypeCreate,
    DictTypeUpdate,
)
from app.rz.models.dict_item import (
    DictItemPublic,
    DictItemsPublic,
    DictItemCreate,
    DictItemCreateSimple,
    DictItemUpdate,
)
from app.rz.crud import dict_crud

router = APIRouter(prefix="/dict", tags=["dictionary"])


# DictType endpoints
@router.get("/types", response_model=list[DictTypePublic])
def list_dict_types(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = Query(default=True, description="Only return enabled types"),
) -> Any:
    """获取字典类型列表"""
    types = dict_crud.get_dict_types(
        session=session, skip=skip, limit=limit, enabled_only=enabled_only
    )
    return types


@router.get("/types/{type_id}", response_model=DictTypePublic)
def get_dict_type(
    session: SessionDep,
    type_id: uuid.UUID,
    enabled_only: bool = Query(default=True, description="Only return enabled items"),
) -> Any:
    """根据ID获取字典类型"""
    dict_type = dict_crud.get_dict_type(session=session, type_id=type_id, enabled_only=enabled_only)
    if not dict_type:
        raise HTTPException(status_code=404, detail="Dictionary type not found")
    return dict_type


@router.get("/types/code/{type_code}", response_model=DictTypePublic)
def get_dict_type_by_code(
    session: SessionDep,
    type_code: str,
    enabled_only: bool = Query(default=True, description="Only return enabled items"),
) -> Any:
    """根据类型代码获取字典类型"""
    dict_type = dict_crud.get_dict_type_by_code(session=session, type_code=type_code, enabled_only=enabled_only)
    if not dict_type:
        raise HTTPException(status_code=404, detail="Dictionary type not found")
    return dict_type

@router.post("/types", response_model=DictTypePublic)
def create_dict_type(
    *,
    session: SessionDep,
    type_in: DictTypeCreate,
) -> Any:
    """创建字典类型"""
    # Check if type_code already exists
    existing = dict_crud.get_dict_type_by_code(session=session, type_code=type_in.type_code)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Dictionary type with code '{type_in.type_code}' already exists",
        )
    
    dict_type = dict_crud.create_dict_type(session=session, dict_type_in=type_in)
    return dict_type


@router.put("/types/{type_id}", response_model=DictTypePublic)
def update_dict_type(
    *,
    session: SessionDep,
    type_id: uuid.UUID,
    type_in: DictTypeUpdate,
) -> Any:
    """更新字典类型"""
    dict_type = dict_crud.get_dict_type(session=session, type_id=type_id)
    if not dict_type:
        raise HTTPException(status_code=404, detail="Dictionary type not found")
    
    # If updating type_code, check for duplicates
    if type_in.type_code and type_in.type_code != dict_type.type_code:
        existing = dict_crud.get_dict_type_by_code(session=session, type_code=type_in.type_code)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Dictionary type with code '{type_in.type_code}' already exists",
            )
    
    updated_type = dict_crud.update_dict_type(
        session=session, db_dict_type=dict_type, dict_type_in=type_in
    )
    return updated_type


@router.delete("/types/{type_id}")
def delete_dict_type(
    session: SessionDep,
    type_id: uuid.UUID,
    cascade: bool = Query(default=False, description="是否删除 dict items"),
    hard_delete: bool = Query(default=False, description="是否硬删除 (default: soft delete)"),
) -> Message:
    """删除字典类型
    
    Args:
        type_id: 字典类型ID
        cascade: 是否级联删除所有字典项（默认False，会检查是否有关联项）
        hard_delete: 是否硬删除（默认False，软删除）
    """
    dict_type = dict_crud.get_dict_type(session=session, type_id=type_id)
    if not dict_type:
        raise HTTPException(status_code=404, detail="Dictionary type not found")
    
    # Check if there are items associated with this type
    count = dict_crud.count_dict_items_by_type(session=session, type_id=type_id)
    
    if count > 0:
        if not cascade:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete dictionary type with {count} associated items. Use cascade=true to delete all items.",
            )
        # Cascade delete items
        deleted_count = dict_crud.cascade_delete_dict_items(
            session=session, type_id=type_id, hard_delete=hard_delete
        )
    
    dict_crud.delete_dict_type(session=session, db_dict_type=dict_type, hard_delete=hard_delete)
    
    delete_type = "permanently deleted" if hard_delete else "soft deleted"
    if count > 0 and cascade:
        return Message(message=f"Dictionary type {delete_type} successfully with {count} items")
    return Message(message=f"Dictionary type {delete_type} successfully")


# DictItem endpoints
@router.get("/items", response_model=DictItemsPublic)
def list_dict_items(
    session: SessionDep,
    type_id: uuid.UUID | None = Query(default=None, description="Filter by type ID"),
    type_code: str | None = Query(default=None, description="Filter by type code"),
    enabled_only: bool = Query(default=True, description="Only return enabled items"),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """获取字典项列表"""
    items, count = dict_crud.get_dict_items(
        session=session,
        type_id=type_id,
        type_code=type_code,
        enabled_only=enabled_only,
        skip=skip,
        limit=limit,
    )
    return DictItemsPublic(data=items, count=count)


@router.get("/items/{item_id}", response_model=DictItemPublic)
def get_dict_item(
    session: SessionDep,
    item_id: uuid.UUID,
) -> Any:
    """根据ID获取字典项"""
    item = dict_crud.get_dict_item(session=session, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Dictionary item not found")
    return item

@router.post("/items", response_model=DictItemPublic)
def create_dict_item(
    *,
    session: SessionDep,
    item_in: DictItemCreate,
) -> Any:
    """创建字典项"""
    # Verify type_id exists
    dict_type = dict_crud.get_dict_type(session=session, type_id=item_in.type_id)
    if not dict_type:
        raise HTTPException(status_code=404, detail="Dictionary type not found")
    
    # Check for duplicate item_code within the same type
    existing = dict_crud.get_dict_item_by_code(session=session, type_code=dict_type.type_code, item_code=item_in.item_code)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Dictionary item with code '{item_in.item_code}' already exists in type '{dict_type.type_code}'",
        )
    
    item = dict_crud.create_dict_item(session=session, dict_item_in=item_in)
    return item


@router.put("/items/{item_id}", response_model=DictItemPublic)
def update_dict_item(
    *,
    session: SessionDep,
    item_id: uuid.UUID,
    item_in: DictItemUpdate,
) -> Any:
    """更新字典项"""
    item = dict_crud.get_dict_item(session=session, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Dictionary item not found")
    
    updated_item = dict_crud.update_dict_item(
        session=session, db_dict_item=item, dict_item_in=item_in
    )
    
    return updated_item


@router.delete("/items/{item_id}")
def delete_dict_item(
    session: SessionDep,
    item_id: uuid.UUID,
    hard_delete: bool = Query(default=False, description="Permanently delete (default: soft delete)"),
) -> Message:
    """删除字典项
    
    Args:
        item_id: 字典项ID
        hard_delete: 是否硬删除（默认False，软删除）
    """
    item = dict_crud.get_dict_item(session=session, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Dictionary item not found")
    
    dict_crud.delete_dict_item(session=session, db_dict_item=item, hard_delete=hard_delete)
    
    delete_type = "permanently deleted" if hard_delete else "soft deleted"
    return Message(message=f"Dictionary item {delete_type} successfully")


# Simplified DictItem endpoints (using type_code and item_code)
@router.get("/{type_code}/items", response_model=DictItemsPublic)
def list_dict_items_by_code(
    session: SessionDep,
    type_code: str,
    enabled_only: bool = Query(default=True, description="Only return enabled items"),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """根据类型代码获取字典项列表（简化接口）"""
    items, count = dict_crud.get_dict_items_by_type_code(
        session=session,
        type_code=type_code,
        enabled_only=enabled_only,
        skip=skip,
        limit=limit,
    )
    return DictItemsPublic(data=items, count=count)


@router.post("/{type_code}/items", response_model=DictItemPublic)
def create_dict_item_by_code(
    *,
    session: SessionDep,
    type_code: str,
    item_in: DictItemCreateSimple,
) -> Any:
    """通过类型代码创建字典项（简化接口）"""
    # Verify type_code exists
    dict_type = dict_crud.get_dict_type_by_code(session=session, type_code=type_code)
    if not dict_type:
        raise HTTPException(status_code=404, detail=f"Dictionary type '{type_code}' not found")
    
    # Check for duplicate item_code within the same type
    existing = dict_crud.get_dict_item_by_code(
        session=session, type_code=type_code, item_code=item_in.item_code
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Dictionary item with code '{item_in.item_code}' already exists in type '{type_code}'",
        )
    
    # Create DictItemCreate with type_id
    item_create = DictItemCreate(
        type_id=dict_type.id,
        item_code=item_in.item_code,
        item_value=item_in.item_value,
        sort_order=item_in.sort_order,
        is_enabled=item_in.is_enabled,
    )
    
    item = dict_crud.create_dict_item(session=session, dict_item_in=item_create)
    return item


@router.get("/{type_code}/items/{item_code}", response_model=DictItemPublic)
def get_dict_item_by_code(
    session: SessionDep,
    type_code: str,
    item_code: str,
    enabled_only: bool = Query(default=True, description="Only return enabled items"),
) -> Any:
    """通过类型代码和项代码获取字典项（简化接口）"""
    item = dict_crud.get_dict_item_by_code(
        session=session, type_code=type_code, item_code=item_code
    )
    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"Dictionary item '{item_code}' not found in type '{type_code}'",
        )
    
    # Filter by enabled status if requested
    if enabled_only and not item.is_enabled:
        raise HTTPException(
            status_code=404,
            detail=f"Dictionary item '{item_code}' not found in type '{type_code}'",
        )
    
    return item


@router.put("/{type_code}/items/{item_code}", response_model=DictItemPublic)
def update_dict_item_by_code(
    *,
    session: SessionDep,
    type_code: str,
    item_code: str,
    item_in: DictItemUpdate,
) -> Any:
    """通过类型代码和项代码更新字典项（简化接口）"""
    item = dict_crud.get_dict_item_by_code(
        session=session, type_code=type_code, item_code=item_code
    )
    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"Dictionary item '{item_code}' not found in type '{type_code}'",
        )
    
    updated_item = dict_crud.update_dict_item(
        session=session, db_dict_item=item, dict_item_in=item_in
    )
    return updated_item


@router.delete("/{type_code}/items/{item_code}")
def delete_dict_item_by_code(
    session: SessionDep,
    type_code: str,
    item_code: str,
    hard_delete: bool = Query(default=False, description="Permanently delete (default: soft delete)"),
) -> Message:
    """通过类型代码和项代码删除字典项（简化接口）
    
    Args:
        type_code: 字典类型代码
        item_code: 字典项代码
        hard_delete: 是否硬删除（默认False，软删除）
    """
    item = dict_crud.get_dict_item_by_code(
        session=session, type_code=type_code, item_code=item_code
    )
    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"Dictionary item '{item_code}' not found in type '{type_code}'",
        )
    
    dict_crud.delete_dict_item(session=session, db_dict_item=item, hard_delete=hard_delete)
    
    delete_type = "permanently deleted" if hard_delete else "soft deleted"
    return Message(message=f"Dictionary item {delete_type} successfully")

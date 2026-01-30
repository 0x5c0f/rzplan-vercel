"""Dictionary item models"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


from app.rz.utils.utils import get_datetime_utc

# Database model
class DictItem(SQLModel, table=True):
    """Dictionary items (key-value pairs)
    
    Stores actual dictionary values associated with dictionary types
    """
    __tablename__ = "dict_item"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    type_id: uuid.UUID = Field(foreign_key="dict_type.id", nullable=False)
    item_code: str = Field(index=True, max_length=100)
    item_value: str = Field(max_length=500)
    sort_order: int = Field(default=0)
    is_enabled: bool = Field(default=True)
    extra_data: str | None = Field(default=None)  # JSON format for additional data
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


# API models
class DictItemBase(SQLModel):
    """Base properties for DictItem"""
    item_code: str = Field(max_length=100)
    item_value: str = Field(max_length=500)
    sort_order: int = 0
    is_enabled: bool = True


class DictItemCreate(DictItemBase):
    """Properties to receive on DictItem creation"""
    type_id: uuid.UUID


class DictItemCreateSimple(SQLModel):
    """Simplified properties to receive on DictItem creation (without type_id)"""
    item_code: str = Field(max_length=100)
    item_value: str = Field(max_length=500)
    sort_order: int = 0
    is_enabled: bool = True
    extra_data: str | None = None


class DictItemUpdate(SQLModel):
    """Properties to receive on DictItem update"""
    item_value: str | None = Field(default=None, max_length=500)
    sort_order: int | None = None
    is_enabled: bool | None = None
    extra_data: str | None = None


class DictItemPublic(DictItemBase):
    """Properties to return via API"""
    id: uuid.UUID
    type_id: uuid.UUID
    extra_data: str | None
    created_at: datetime
    updated_at: datetime


class DictItemsPublic(SQLModel):
    """Paginated list of dictionary items"""
    data: list[DictItemPublic]
    count: int

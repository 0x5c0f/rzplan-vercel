"""Dictionary type models"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel

from app.rz.utils.utils import get_datetime_utc

# Database model
class DictType(SQLModel, table=True):
    """Dictionary type definitions
    
    Stores different types of dictionaries
    """
    __tablename__ = "dict_type"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    type_code: str = Field(unique=True, index=True, max_length=50)
    type_name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_enabled: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


# API models
class DictTypeBase(SQLModel):
    """Base properties for DictType"""
    type_code: str = Field(max_length=50)
    type_name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_enabled: bool = True


class DictTypeCreate(DictTypeBase):
    """Properties to receive on DictType creation"""
    pass


class DictTypeUpdate(SQLModel):
    """Properties to receive on DictType update"""
    type_code: str | None = Field(default=None, max_length=50)
    type_name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_enabled: bool | None = None


class DictTypePublic(DictTypeBase):
    """Properties to return via API"""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

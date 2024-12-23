import uuid
import re
from sqlmodel import Field, SQLModel, Relationship  # type: ignore
from typing import TYPE_CHECKING, List, Optional
from pydantic import field_validator

if TYPE_CHECKING:
    from app.rz.models.performance_data import PerformanceData

# Shared properties for performance tracking configuration
class PerformanceTrackingConfigBase(SQLModel):
    tracking_domain: str = Field(unique=True, nullable=False, max_length=191)
    tracking_code: str = Field(unique=True, nullable=False, max_length=191)
    is_active: bool = Field(default=True)
    
    @field_validator('tracking_domain')
    def validate_tracking_domain(cls, value):
        domain_regex = r'^([0-9a-zA-Z-]{1,}\.)+([a-zA-Z]{2,})$'
        if not re.match(domain_regex, value):
            raise ValueError('tracking_domain 必须是一个有效的域名')
        return value

    @field_validator('tracking_code')
    def validate_tracking_code(cls, value):
        if len(value) < 12:
            raise ValueError('tracking_code 长度应该大于11')
        
        code_regex = r'^[a-zA-Z0-9-]+$'
        if not re.match(code_regex, value):
            raise ValueError('tracking_code 必须是一个有效的字符串')
        return value

class PerformanceTrackingConfigCreate(SQLModel):
    tracking_domain: str = Field(nullable=False, max_length=191)
    tracking_code: Optional[str] = None  # 可选字段
    is_active: Optional[bool] = None  # 可选布尔字段
    
class PerformanceTrackingUpdate(SQLModel):
    tracking_code: str = Field(nullable=True, unique=True,max_length=191)
    is_active: bool = Field(nullable=True)
    id: uuid.UUID

# Database model, database table inferred from class name
class PerformanceTrackingConfig(PerformanceTrackingConfigBase, table=True):
    __tablename__ = "performance_tracking_config"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    performance_data: List["PerformanceData"] = Relationship(back_populates="tracking_config")

# Properties to return via API, id is always required
class PerformanceTrackingConfigPublic(PerformanceTrackingConfigBase):
    tracking_code: str
    tracking_domain: str
    id: uuid.UUID

class PerformanceTrackingConfigsPublic(SQLModel):
    data: list[PerformanceTrackingConfigPublic]
    count: int

# Generic message for response
class Message(SQLModel):
    message: str

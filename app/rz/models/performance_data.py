import uuid
from datetime import datetime,timezone
from sqlmodel import Field, SQLModel, Relationship  # type: ignore
from app.rz.models.performance_tracking_config import PerformanceTrackingConfig  # noqa: E402

from sqlalchemy.sql import func

# Shared properties for performance data
class PerformanceDataBase(SQLModel):
    dns_time: float = Field(description="DNS查询时间")
    redirect_time: float = Field(description="重定向时间")
    dom_load_time: float = Field(description="DOM结构解析时间")
    frontend_performance: float = Field(description="页面完全加载时间")
    ttfb_time: float = Field(description="读取页面第一个字节时间")
    content_load_time: float = Field(description="内容加载时间")
    onload_callback_time: float = Field(description="执行onload回调函数时间")
    dns_cache_time: float = Field(description="DNS缓存时间")
    unload_time: float = Field(description="卸载页面时间")
    tcp_handshake_time: float = Field(description="TCP握手时间")
    request_uri: str = Field(description="请求URI")
    
class PerformanceDataValidate(PerformanceDataBase):
    tracking_code: str = Field(description="跟踪码")
    tracking_domain: str = Field(description="跟踪域名")
    
class PerformanceDataInsert(PerformanceDataBase):
    tracking_domain: str = Field(description="跟踪域名")

# Database model, database table inferred from class name
class PerformanceData(PerformanceDataBase, table=True):
    __tablename__ = "performance_data"
    
    tracking_domain: str = Field(foreign_key="performance_tracking_config.tracking_domain", description="关联的域名")
    
    created_at: datetime = Field(
    default_factory=lambda: datetime.now(timezone.utc),  # 使用 timezone.utc 获取当前 UTC 时间
    sa_column_kwargs={
        "server_default": func.now(),
        "nullable": False
    },
    description="创建时间"
)

    # created_at = Column(DateTime, default=func.now(), info={'description':'创建时间'})
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tracking_config: "PerformanceTrackingConfig" = Relationship(back_populates="performance_data")

# Properties to return via API, id is always required
class PerformanceDataPublic(PerformanceDataBase):
    tracking_domain: str
    id: uuid.UUID

class PerformanceDatasPublic(SQLModel):
    data: list[PerformanceDataPublic]
    count: int

# Generic message for response
class Message(SQLModel):
    message: str

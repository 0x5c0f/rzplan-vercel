import uuid
from sqlmodel import Field, SQLModel
from datetime import datetime, timezone

from sqlalchemy.sql import func

class DifyChatLogBase(SQLModel):
    dify_user_id: str = Field(max_length=50, nullable=False,description="dify user id")
    dify_app_id: str = Field(max_length=50, nullable=False,description="dify app id")
    user_name: str = Field(max_length=50, nullable=True,description="用户姓名")
    user_contact: str = Field(max_length=50, nullable=True, description="用户联系方式")
    ask: str = Field(nullable=True,description="提问")  
    answer: str = Field(nullable=True,description="AI回答")

class DifyChatLogCreate(DifyChatLogBase):
    pass

class DifyChatLogUpdate(SQLModel):
    id: uuid.UUID

class DifyChatLog(DifyChatLogBase, table=True):
    __tablename__ = "dify_chat_log"

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),  # 使用 timezone.utc 获取当前 UTC 时间
        sa_column_kwargs={
            "server_default": func.now(),
            "nullable": False
        },
        description="创建时间"
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
class DifyChatLogPublic(DifyChatLogBase):
    created_at: datetime
    id: uuid.UUID

class DifyChatLogsPublic(SQLModel):
    data: list[DifyChatLogPublic]
    count: int

# Generic message for response
class Message(SQLModel):
    message: str
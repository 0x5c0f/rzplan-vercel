from uuid import UUID
from typing import Any, List

from fastapi import APIRouter, HTTPException, Depends
from app.api.deps import SessionDep
from app.rz.crud import dify_chat_log as crud
from app.rz.models.dify_chat_log import DifyChatLogPublic,DifyChatLogCreate,DifyChatLogsPublic  # Assuming the model is defined in this path

router = APIRouter(prefix="/dify/chat_data", tags=["dify"])

@router.post("/", response_model=DifyChatLogPublic)
def create_chat_log(
    *,
    session: SessionDep,
    chat_log: DifyChatLogCreate
) -> Any:
    """
    创建新的聊天记录
    """
    return crud.create_dify_chat_log(session=session, chat_log=chat_log)

@router.get("/", response_model=DifyChatLogsPublic)
def read_all_chat_logs(
    session: SessionDep,
    skip: int = 0,
    limit: int = 10
) -> Any:
    """
    获取所有聊天记录
    """
    
    data = crud.get_all_dify_chat_logs(session=session, skip=skip, limit=limit)
    return DifyChatLogsPublic(data=data,count=len(data))

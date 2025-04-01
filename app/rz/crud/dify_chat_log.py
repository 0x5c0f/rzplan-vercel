from typing import List
from sqlmodel import Session, select
from app.rz.models.dify_chat_log import DifyChatLog,DifyChatLogBase  # Assuming the model is defined in this path
from uuid import UUID

def create_dify_chat_log(session: Session, chat_log: DifyChatLogBase) -> DifyChatLog:
    db_chat_log = DifyChatLog.model_validate(chat_log)
    session.add(db_chat_log)
    session.commit()
    session.refresh(db_chat_log)
    return db_chat_log

def get_all_dify_chat_logs(session: Session, skip: int = 0, limit: int = 10) -> List[DifyChatLog]:
    return list(session.exec(select(DifyChatLog).offset(skip).limit(limit)).all())

def delete_dify_chat_log(session: Session, chat_log_id: UUID) -> None:
    chat_log = session.get(DifyChatLog, chat_log_id)
    if chat_log:
        session.delete(chat_log)
        session.commit()

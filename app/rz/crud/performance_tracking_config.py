from uuid import UUID
from sqlmodel import Session, select
from typing import List
from app.rz.models.performance_tracking_config import (
    PerformanceTrackingConfig,
    PerformanceTrackingConfigBase,
    PerformanceTrackingUpdate,
)

from pydantic import ValidationError
from fastapi import HTTPException

def create_tracking_config(session: Session, config: PerformanceTrackingConfigBase) -> PerformanceTrackingConfig:
    """
    创建新的性能跟踪配置并保存到数据库。

    :param session: 数据库会话对象
    :param config: 性能跟踪配置的基本数据
    :return: 创建的 PerformanceTrackingConfig 对象
    """
    # db_config = PerformanceTrackingConfig(**config.model_dump())
    try:
        db_config = PerformanceTrackingConfig.model_validate(config.model_dump())
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    session.add(db_config)
    session.commit()
    session.refresh(db_config)
    return db_config

def get_tracking_config(session: Session, tracking_domain: str , tracking_code: str) -> PerformanceTrackingConfig | None:
    """
    根据跟踪域和跟踪代码获取性能跟踪配置。

    :param session: 数据库会话对象
    :param tracking_domain: 跟踪域
    :param tracking_code: 跟踪代码
    :return: 匹配的 PerformanceTrackingConfig 对象或 None
    """
    return session.exec(
        select(PerformanceTrackingConfig).where(
            PerformanceTrackingConfig.tracking_domain == tracking_domain, 
            PerformanceTrackingConfig.tracking_code == tracking_code
        )
    ).first()
    
def get_all_tracking_configs(session: Session, skip: int = 0, limit: int = 10) -> List[PerformanceTrackingConfig]:
    """
    获取所有性能跟踪配置，支持分页。

    :param session: 数据库会话对象
    :param skip: 跳过的记录数
    :param limit: 获取的最大记录数
    :return: 性能跟踪配置列表
    """
    return list(session.exec(select(PerformanceTrackingConfig).offset(skip).limit(limit)).all())


def get_tracking_config_by_id(session: Session, config_id: UUID) -> PerformanceTrackingConfig | None:
    """
    根据配置 ID 获取性能跟踪配置。

    :param session: 数据库会话对象
    :param config_id: 配置的 UUID
    :return: 匹配的 PerformanceTrackingConfig 对象或 None
    """
    return session.get(PerformanceTrackingConfig, config_id)

def get_tracking_config_by_domain(session: Session, tracking_domain: str) -> PerformanceTrackingConfig | None:
    """
    根据跟踪域获取性能跟踪配置。

    :param session: 数据库会话对象
    :param tracking_domain: 跟踪域
    :return: 匹配的 PerformanceTrackingConfig 对象或 None
    """
    return session.exec(select(PerformanceTrackingConfig).where(PerformanceTrackingConfig.tracking_domain == tracking_domain)).first()
    # return session.get(PerformanceTrackingConfig, tracking_domain)

def get_tracking_config_by_code(session: Session, code: str) -> PerformanceTrackingConfig | None:
    """
    根据跟踪代码获取性能跟踪配置。

    :param session: 数据库会话对象
    :param code: 跟踪代码
    :return: 匹配的 PerformanceTrackingConfig 对象或 None
    """
    return session.exec(select(PerformanceTrackingConfig).where(PerformanceTrackingConfig.tracking_code == code)).first()

def get_tracking_config_by_code_and_domain(session: Session, tracking_domain: str, tracking_code: str) -> PerformanceTrackingConfig | None:
    """
    根据跟踪代码和跟踪域获取性能跟踪配置。

    :param session: 数据库会话对象
    :param code: 跟踪代码
    :param tracking_domain: 跟踪域
    :return: 匹配的 PerformanceTrackingConfig 对象或 None
    """
    return session.exec(
        select(PerformanceTrackingConfig).where(
            PerformanceTrackingConfig.tracking_code == tracking_code, 
            PerformanceTrackingConfig.tracking_domain == tracking_domain
            # PerformanceTrackingConfig.is_active == True
            )
    ).first()

def update_tracking_config(session: Session, db_config: PerformanceTrackingConfig, config_update: PerformanceTrackingUpdate) -> PerformanceTrackingConfig:
    """
    更新现有的性能跟踪配置。

    :param session: 数据库会话对象
    :param db_config: 待更新的 PerformanceTrackingConfig 对象
    :param config_update: 包含更新数据的 PerformanceTrackingUpdate 对象
    :return: 更新后的 PerformanceTrackingConfig 对象
    """
    update_data = config_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config, key, value)
    session.add(db_config)
    session.commit()
    session.refresh(db_config)
    return db_config

def delete_tracking_config(session: Session, config_id: UUID) -> None:
    """
    根据配置 ID 删除性能跟踪配置。

    :param session: 数据库会话对象
    :param config_id: 配置的 UUID
    """
    config = session.get(PerformanceTrackingConfig, config_id)
    if config:
        session.delete(config)
        session.commit()

def disable_tracking_config(session: Session, config_id: UUID) -> PerformanceTrackingConfig:
    """
    禁用性能跟踪配置。

    :param session: 数据库会话对象
    :param config_id: 配置的 UUID
    :return: 更新后的 PerformanceTrackingConfig 对象
    """
    config = session.get(PerformanceTrackingConfig, config_id)
    if config:
        config.is_active = False
        session.add(config)
        session.commit()
        session.refresh(config)
        return config
from typing import List
from sqlmodel import Session, select
from app.rz.models.performance_data import PerformanceData,PerformanceTrackingConfig

from sqlmodel import func
from datetime import datetime, timedelta, timezone

from uuid import UUID

def create_performance_data(session: Session, data: PerformanceData) -> PerformanceData:
    db_data = PerformanceData.model_validate(data)
    session.add(db_data)
    session.commit()
    session.refresh(db_data)
    return db_data

def get_performance_data(session: Session, data_id: UUID) -> PerformanceData | None:
    return session.get(PerformanceData, data_id)

def get_all_performance_data(session: Session, skip: int = 0, limit: int = 10) -> List[PerformanceData]:
    # return session.exec(select(PerformanceData).offset(skip).limit(limit)).all()
    return list(session.exec(select(PerformanceData).offset(skip).limit(limit)).all())

def delete_performance_data(session: Session, data_id: UUID) -> None:
    data = session.get(PerformanceData, data_id)
    if data:
        session.delete(data)
        session.commit()

def get_performance_data_by_domain(session: Session, tracking_domain: str, skip: int = 0, limit: int = 10,tracking_is_active: bool = None) -> List[PerformanceData]:
    
    query = select(PerformanceData).join(
        PerformanceTrackingConfig,
        PerformanceData.tracking_domain == PerformanceTrackingConfig.tracking_domain
    )
   
    if tracking_is_active is not None:
        query = query.where(
            PerformanceData.tracking_domain == tracking_domain, 
            PerformanceTrackingConfig.is_active == tracking_is_active
        )
    else:
        query = query.where(
            PerformanceData.tracking_domain == tracking_domain
        )
    return list(session.exec(query.offset(skip).limit(limit)).all())
    
    # return list(session.exec(select(PerformanceData).where(PerformanceData.tracking_domain == tracking_domain).offset(skip).limit(limit)).all())


def get_all_performance_data_for_metrics(session: Session, tracking_domain: str = None, time_interval: int = 30):
    time_threshold = datetime.now(timezone.utc) - timedelta(minutes=time_interval)
    
    # 创建子查询，获取每个 request_uri, tracking_domain 组合的最新创建时间
    subquery = (
        select(
            PerformanceData.request_uri,
            PerformanceData.tracking_domain,
            func.max(PerformanceData.created_at).label('max_created_at')
        )
        .join(
            PerformanceTrackingConfig,
            PerformanceData.tracking_domain == PerformanceTrackingConfig.tracking_domain
        )
        .where(
            PerformanceData.created_at >= time_threshold,
            PerformanceTrackingConfig.is_active == True  # 在子查询中加入 is_active 条件
        )
    )
    
    if tracking_domain:
        subquery = subquery.where(PerformanceData.tracking_domain == tracking_domain)
    
    subquery = subquery.group_by(
        PerformanceData.request_uri,
        PerformanceData.tracking_domain
    ).subquery()

    # 使用子查询联结获取最新的 PerformanceData 记录
    latest_data_query = (
        select(PerformanceData)
        .join(
            subquery,
            (PerformanceData.request_uri == subquery.c.request_uri) &
            (PerformanceData.created_at == subquery.c.max_created_at)
        )
        .join(
            PerformanceTrackingConfig,
            PerformanceData.tracking_domain == PerformanceTrackingConfig.tracking_domain
        )
        .where(PerformanceTrackingConfig.is_active == True)  # 进一步确保 is_active 条件
    )

    return session.exec(latest_data_query).all()
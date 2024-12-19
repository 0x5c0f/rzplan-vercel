from uuid import UUID
from typing import Any

from fastapi import APIRouter, HTTPException, Depends

from app.api.deps import SessionDep, get_current_active_superuser
from app.rz.crud import performance_tracking_config as crud

from app.rz.utils.utils import generate_random_string

from app.rz.models.performance_tracking_config import (
    PerformanceTrackingConfig,
    PerformanceTrackingUpdate,
    PerformanceTrackingConfigPublic,
    PerformanceTrackingConfigsPublic,
    PerformanceTrackingConfigCreate,
)

router = APIRouter(prefix="/performance/webpage/tracking_config", tags=["performance_tracking_config"])

@router.post("/", 
        response_model=PerformanceTrackingConfigPublic,
        dependencies=[Depends(get_current_active_superuser)]
)
def create_tracking_config(
    *,
    session: SessionDep,
    config_in: PerformanceTrackingConfigCreate,
) -> Any:
    """
    创建一个跟踪配置
    \n tracking_code:      跟踪代码, 为空自动生成, 长度大于12位 
    \n tracking_domain:    跟踪域名
    \n is_active:          是否启用，可选，默认启用
    """
    # 检查域名是否存在
    existing_domain = crud.get_tracking_config_by_domain(
        session=session, 
        tracking_domain=config_in.tracking_domain
    )
    if existing_domain:
        raise HTTPException(
            status_code=400,
            detail="The tracking tracking_domain already exists in the system.",
        )
        
    if config_in.is_active is None:
        config_in.is_active = True
    
    if config_in.tracking_code:
        # 检查code是否存在
        existing_code = crud.get_tracking_config_by_code(
            session=session, 
            code=config_in.tracking_code
        )
        if existing_code:
            raise HTTPException(
                status_code=400,
                detail="The tracking code already exists in the system.",
            )
    else:
        while True:
            random_tracking_code = generate_random_string(length=12)
            existing_code = crud.get_tracking_config_by_code(
                session=session,
                code=random_tracking_code
            )
            if not existing_code:
                config_in.tracking_code = random_tracking_code
                break
        
    config = crud.create_tracking_config(session=session, config=config_in)
    return config

@router.get("/", response_model=PerformanceTrackingConfigsPublic, dependencies=[Depends(get_current_active_superuser)])
def read_tracking_configs(
    session: SessionDep,
    skip: int = 0,
    limit: int = 10
) -> Any:
    """
    获取所有跟踪配置
    """
    data = crud.get_all_tracking_configs(session=session, skip=skip, limit=limit)
    return PerformanceTrackingConfigsPublic(data=data, count=len(data))

@router.get("/tracking_id/{config_id}", response_model=PerformanceTrackingConfigPublic, dependencies=[Depends(get_current_active_superuser)])
def read_tracking_config(
    *,
    session: SessionDep,
    config_id: UUID
) -> Any:
    """
    根据配置ID获取跟踪配置
    """
    config = crud.get_tracking_config_by_id(session=session, config_id=config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Tracking config not found")
    return config

@router.get("/tracking_domain/{tracking_domain}", response_model=PerformanceTrackingConfig)
def read_tracking_config_by_domain(
    *,
    session: SessionDep,
    tracking_domain: str
) -> Any:
    """
    根据跟踪域名获取跟踪配置
    """
    config = crud.get_tracking_config_by_domain(session=session, tracking_domain=tracking_domain)
    if not config:
        raise HTTPException(status_code=404, detail="Tracking config not found")
    return config
    
    
@router.put("/", response_model=PerformanceTrackingConfigPublic, dependencies=[Depends(get_current_active_superuser)])
def update_tracking_config(
    *,
    session: SessionDep,
    config_in: PerformanceTrackingUpdate,
) -> Any:
    """
    更新跟踪配置
    \n config_id: 跟踪配置ID
    \n config_in: 跟踪配置信息
    \n tracking_code: 跟踪代码
    """
    config = crud.get_tracking_config_by_id(session=session, config_id=config_in.id)
    if not config:
        raise HTTPException(status_code=404, detail="Tracking config not found")
    
    code_exists = crud.get_tracking_config_by_code(session=session, code=config_in.tracking_code)
    if code_exists and code_exists.id != config_in.id:
        raise HTTPException(status_code=400, detail="Tracking code already exists")
    
    config = crud.update_tracking_config(session=session, db_config=config, config_update=config_in)
    return config

@router.delete("/{config_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_tracking_config(
    session: SessionDep,
    config_id: UUID,
    is_physical_delete: bool = False
) -> Any:
    """
    删除或者禁用跟踪配置
    \n is_physical_delete: 是否物理删除
    \n config_id: 跟踪配置ID
    """
    config = crud.get_tracking_config_by_id(session=session, config_id=config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Tracking config not found")
    
    if is_physical_delete:
        crud.delete_tracking_config(session=session, config_id=config_id)
        return {"detail": "Tracking config deleted successfully"}
    else:
        return crud.disable_tracking_config(session=session, config_id=config_id)
from uuid import UUID
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import Response

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.api.deps import SessionDep, get_current_active_superuser
from app.rz.crud import performance_data as crud
from app.rz.models.performance_data import (
    PerformanceDataValidate,
    PerformanceDataInsert,
    PerformanceDataPublic,
    PerformanceDatasPublic,
)
from app.rz.crud import performance_tracking_config as config_crud

from app.rz.utils.utils import performance_data_metrics, generate_pcheck_js_file

from app.core.config import settings


router = APIRouter()

# 调用函数以创建指标和注册表
metrics, registry = performance_data_metrics()


@router.get("/pcheck.js")
def view_pcheckjs():
    """
    ```js
    <script id="performance-check-script" src="//{{ DOMAIN }}{{ API_V1_STR }}/performance/webpage/data/pcheck.js" data-tracking-code="{{ TRACKING_CODE }}"></script>
    ```
    """
    filepath = "app/rz/templates/pcheck.js"
    
    rendered_content = generate_pcheck_js_file(
        filepath, 
        DOMAIN=settings.DOMAIN, 
        ENABLELOG=str(settings.LOG_LEVEL == 'DEBUG').lower(), 
        API_V1_STR=settings.API_V1_STR
    )
    
    headers = {
        "Cache-Control": "public, max-age=604800",
        "ETag": "unique-file-version",
        "Content-Type": "application/javascript; charset=utf-8,gb2312,gbk",
    }
    
    return Response(rendered_content, media_type='application/javascript',headers=headers)

@router.get("/metrics")
def read_performance_data_metrics(
    *,
    session: SessionDep,
    tracking_domain: str = Query(None, alias="target", description="Filter metrics by tracking_domain"),
    time_interval: int = Query(30, gt=0, description="Time interval in minutes, must be greater than 0")
) -> Any:
    """
    Performance data metrics
    """

    # latest_data_list = crud.get_performance_data_by_domain(session=session, tracking_domain=tracking_domain)
    latest_data_list = crud.get_all_performance_data_for_metrics(session=session,tracking_domain=tracking_domain,time_interval=time_interval)


    if not latest_data_list:
        raise HTTPException(status_code=404, detail=f"No page load time data found for tracking_domain '{tracking_domain}' within the last {time_interval} minutes.")
    
    # 动态更新 Prometheus 指标，带有多个标签
    for latest in latest_data_list:
        tracking_domain = latest.tracking_domain
        request_uri = str(latest.request_uri)
        for metric_name, metric_value in metrics.items():
            metric_value.labels(tracking_domain, request_uri).set(getattr(latest, metric_name))
    
    # 生成 Prometheus 格式的响应
    metrics_data = generate_latest(registry)
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)

@router.post("/", response_model=PerformanceDataPublic)
def create_performance_data(
    *,
    session: SessionDep,
    data_in: PerformanceDataValidate
) -> Any:
    """
    创建页面性能分析数据 
    """
    # 检查 tracking_domain 是否存在
    existing_config = config_crud.get_tracking_config_by_code_and_domain(session, data_in.tracking_domain, data_in.tracking_code)
    if not existing_config:
        raise HTTPException(status_code=400, detail=f"'{data_in.tracking_code}' 校验失败，采集配置不存在！")
    
    if existing_config.is_active is False:
        raise HTTPException(status_code=400, detail=f"Tracking Domain '{data_in.tracking_domain}' 采集已禁用！")
    
    # 创建 performance_data 实例 
    performanceDataInsert = PerformanceDataInsert(
        **data_in.model_dump(exclude={"tracking_code", "tracking_domain"}),
        tracking_domain=data_in.tracking_domain
    )
    
    data = crud.create_performance_data(session=session, data=performanceDataInsert)
    return data

@router.get("/", response_model=PerformanceDatasPublic, dependencies=[Depends(get_current_active_superuser)])
def read_performance_data(
    session: SessionDep,
    skip: int = 0,
    limit: int = 10
) -> Any:
    """
    获取所有页面性能分析数据
    """
    data = crud.get_all_performance_data(session=session, skip=skip, limit=limit)
    return PerformanceDatasPublic(data=data, count=len(data))

@router.get("/by-id/{data_id}", response_model=PerformanceDataPublic,dependencies=[Depends(get_current_active_superuser)])
def read_performance_data_by_id(
    *,
    session: SessionDep,
    data_id: UUID
) -> Any:
    """
    通过数据ID获取指定页面性能分析数据
    """
    data = crud.get_performance_data(session=session, data_id=data_id)
    if not data:
        raise HTTPException(status_code=404, detail="Performance data not found")
    return data

@router.get("/by-tracking_domain/{tracking_domain}", response_model=PerformanceDatasPublic,dependencies=[Depends(get_current_active_superuser)])
def read_performance_data_by_domain(
    *,
    session: SessionDep,
    tracking_domain: str,
    tracking_is_active: bool = None,
    skip: int = 0,
    limit: int = 10
) -> Any:
    """
    通过跟踪域名获取指定页面性能分析数据
    """
    data = crud.get_performance_data_by_domain(session=session, tracking_domain=tracking_domain, skip=skip, limit=limit,tracking_is_active=tracking_is_active)
    return PerformanceDatasPublic(data=data, count=len(data))


## TODO: 不需要删除功能 
# @router.delete("/{data_id}", dependencies=[Depends(get_current_active_superuser)])
# def delete_performance_data(
#     session: SessionDep,
#     data_id: UUID,
# ) -> Any:
#     """
#     Delete performance data.
#     """
#     data = crud.get_performance_data(session=session, data_id=data_id)
#     if not data:
#         raise HTTPException(status_code=404, detail="Performance data not found")
#     crud.delete_performance_data(session=session, data_id=data_id)
#     return {"detail": "Performance data deleted successfully"}
from typing import List, Dict
from fastapi import UploadFile, HTTPException, Form
from app.rz.utils.logger import logger
from app.rz.utils.comfyui.api_controller import ComfyUIController

import json
from app.rz.models.comfyui_workflow import ComfyUIWorkflow, WorkFlowNodeInfo
from pydantic import ValidationError

async def upload_images_to_comfyui(images: List[UploadFile], comfyui_controller: ComfyUIController) -> Dict:
    """
    上传多个图片到ComfyUI服务器
    
    Note:
    - ComfyUI控制器初始化留在路由层处理，因为：
      1. 属于服务连接配置
      2. 可能根据请求参数变化
      3. 保持CRUD只关注核心业务逻辑
    
    Args:
        images: 上传文件列表
        comfyui_controller: 已初始化的ComfyUI控制器实例
        
    Returns:
        dict: 包含上传结果的字典
            {
                "file_mapping": {原文件名: 上传后文件名},
                "upload_details": [
                    {
                        "original_filename": str,
                        "uploaded_filename": str,
                        "status": "success"|"failed",
                        "error": str (如果失败)
                    }
                ]
            }
    """
    file_mapping = {}
    uploaded_files = []
    
    for image in images:
        # 验证文件类型
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail=f"File {image.filename} is not an image"
            )
        
        try:
            uploaded_filename = await comfyui_controller.upload_image_from_file(image)
            file_mapping[image.filename] = uploaded_filename
            uploaded_files.append({
                "original_filename": image.filename,
                "uploaded_filename": uploaded_filename,
                "status": "success"
            })
            logger.debug(f"Successfully uploaded {image.filename} as {uploaded_filename}")
            
        except Exception as upload_error:
            logger.error(f"Failed to upload {image.filename}: {str(upload_error)}")
            uploaded_files.append({
                "original_filename": image.filename,
                "uploaded_filename": None,
                "status": "failed",
                "error": str(upload_error)
            })
    
    return {
        "file_mapping": file_mapping,
        "upload_details": uploaded_files
    }
    
async def parse_workflow_data(data_in: str = Form(...)) -> List[ComfyUIWorkflow]:
    """
    解析工作流数据的依赖项函数
    将 Form 中的 JSON 字符串解析为 ComfyUIWorkflow 列表
    
    支持两种输入格式：
    1. inputs 为字典: {"node_id": 0, "inputs": {"key": "value"}}
    2. inputs 为字典数组: {"node_id": 0, "inputs": [{"key": "value"}]}
    """
    try:
        logger.debug(f"Raw workflow data: {data_in}")
        parsed_data = json.loads(data_in)
        
        workflows = []
        # 统一转换为标准格式
        if isinstance(parsed_data, list):
            for item in parsed_data:
                if isinstance(item.get("inputs"), dict):
                    # 格式1: 将字典转换为数组
                    workflows.append(ComfyUIWorkflow(
                        node_id=item["node_id"],
                        inputs=[WorkFlowNodeInfo(**item["inputs"])]
                    ))
                else:
                    # 格式2: 已经是正确格式
                    workflows.append(ComfyUIWorkflow(
                        node_id=item["node_id"],
                        inputs=[WorkFlowNodeInfo(**i) for i in item["inputs"]]
                    ))
        else:
            if parsed_data:
                workflows.append(ComfyUIWorkflow(
                    node_id=parsed_data["node_id"],
                    inputs=[WorkFlowNodeInfo(**parsed_data["inputs"])]
                    if isinstance(parsed_data["inputs"], dict)
                    else [WorkFlowNodeInfo(**i) for i in parsed_data["inputs"]]
                ))
                
        logger.info(f"Parsed {len(workflows)} workflow items")
        return workflows
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid JSON format: {str(e)}"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=422, 
            detail=f"Data validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error while parsing workflow data: {str(e)}"
        )


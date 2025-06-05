from typing import List, Dict, Optional
from fastapi import UploadFile, HTTPException, Form
from app.rz.utils.logger import logger
from app.rz.utils.comfyui.api_controller import ComfyUIController

import json
from pydantic import ValidationError

from app.rz.models.comfyui_workflow import WorkFlowNodePublic,WorkFlowImageUploadPublic

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
    
async def parse_workflow_data(data_in: str = Form(...)) -> WorkFlowNodePublic:
    """
    解析工作流数据的依赖项函数
    将 Form 中的 JSON 字符串解析为 WorkFlowNodePublic 列表
    """
    try:
        logger.info(f"Received data: {data_in}")
        # 解析 JSON 字符串
        data_dict = json.loads(data_in)
        # 直接使用构造函数，这在 v1 和 v2 中都有效
        return WorkFlowNodePublic(**data_dict)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid JSON format in data_in: {str(e)}"
        )
    except (ValidationError, TypeError) as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Validation error in data_in: {str(e)}"
        )

async def parse_server_info(data_in: Optional[str] = None) -> WorkFlowImageUploadPublic:
    """
    解析服务器信息的依赖项函数
    
    当 data_in 为 None 时返回默认配置
    """
    if data_in is None:
        return WorkFlowImageUploadPublic()
        
    try:
        # 解析 JSON 字符串
        data_dict = json.loads(data_in)
        # 直接使用构造函数，这在 v1 和 v2 中都有效
        return WorkFlowImageUploadPublic(**data_dict)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid JSON format in data_in: {str(e)}"
        )
    except (ValidationError, TypeError) as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Validation error in data_in: {str(e)}"
        )
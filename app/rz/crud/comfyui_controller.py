from typing import List, Dict
from fastapi import UploadFile, HTTPException
from app.rz.utils.logger import logger
from app.rz.utils.comfyui_controller import ComfyUIController

async def upload_images_to_comfyui(
    images: List[UploadFile],
    comfyui_controller: ComfyUIController
) -> Dict:
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
from fastapi import APIRouter,HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse
from app.rz.models.notification import AliyunSMSData
from app.rz.utils.logger import logger

from app.rz.models.tagcloud import TagCloudPublic
from app.rz.utils.utils import tagcloud_generator

from app.rz.utils.utils import aliyun_sms_send

from app.rz.utils.comfyui_controller import ComfyUIController
from app.rz.crud.comfyui_controller import upload_images_to_comfyui
from typing import List, Dict

from app.rz.models.comfyui_workflow import ComfyUIWorkflowPublic

router = APIRouter(prefix="/utils", tags=["utils"])

@router.post("/notify/aliyun_sms/")
async def aliyun_sms(
    AliyunSMSData: AliyunSMSData, 
):
    """
    发送阿里云短信  
    - aliyun_key_data: 阿里云密钥数据
        - access_key_id: 阿里云 access key id
        - access_key_secret: 阿里云 access key secret
    - phone_number: 接收短信的手机号码  
    - sign_name: 短信签名
    - template_code: 短信模板Code
    - template_param: 短信模板变量
        - 参数名: 参数值
    """
    
    try:
        return await aliyun_sms_send(AliyunSMSData)
    except Exception as error:
        logger.error(error.message)
        logger.error(error.data.get("Recommend"))
        raise HTTPException(status_code=400, detail=str(error))
    
@router.post("/tagcloud")
async def generate_tagcloud(
    tag_data: TagCloudPublic
):
    """
    生成标签云图
    
    - Args:
        - tag_data: 标签云配置和数据  
            ```json
            {
                "tags": [
                    {"tag": "Python", "count": 50},
                    {"tag": "Java", "count": 30},
                    {"tag": "C++", "count": 20},
                    {"tag": "机器学习", "count": 40}
                ],
                "font": "Arial",            # 字体, 默认 "Arial" (可选)
                "width": 800,               # 分辨率 (可选)
                "height": 400,              # 分辨率 (可选)
                "background_color": "white" # 背景颜色 (可选)
            }
            ```
    - Returns:  
        - FileResponse: 返回生成的标签云图文件  
    """
    try:
        file_path = await tagcloud_generator(tag_data)
        return FileResponse(
            file_path,
            media_type="image/png",
            filename="tagcloud.png"
        )
    except Exception as e:
        logger.error(f"生成标签云失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"生成标签云失败: {str(e)}"
        )
        

@router.post("/comfyui/upload-image")
async def upload_image_to_comfyui(
    images: List[UploadFile] = File(),
    comfyui_server_host: str = None,
    comfyui_server_port: str = None
) -> Dict:
    """上传图片到comfyui input 目录，返回上传后的文件名与原文件名的对应关系"""
    
    # 构建服务器URL
    if comfyui_server_host and comfyui_server_port:
        comfyui_controller = ComfyUIController(f"{comfyui_server_host}:{comfyui_server_port}")
    else:
        comfyui_controller = ComfyUIController()
    
    try:
        async with comfyui_controller:
            upload_result = await upload_images_to_comfyui(images, comfyui_controller)
            
            return {
                "success": True,
                "message": f"Processed {len(images)} images",
                "server_url": comfyui_controller.server_url,
                "file_mapping": upload_result["file_mapping"],
                "upload_details": upload_result["upload_details"]
            }
            
    except HTTPException:
        raise  # 直接抛出已有的HTTP异常
    except Exception as e:
        logger.error(f"Error during upload process: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        await comfyui_controller.close()
        
@router.post("/comfyui/workflow_queue")
async def workflow_queue(
    data_in: ComfyUIWorkflowPublic,
    workflow: UploadFile = File(), 
) -> Dict:
    """创建工作流队列，并返回结果"""
    pass


## 工作流任务查询
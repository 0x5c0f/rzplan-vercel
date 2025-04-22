from fastapi import APIRouter

from fastapi import APIRouter,HTTPException
from fastapi.responses import FileResponse
from app.rz.models.notification import AliyunSMSData
from app.rz.utils.logger import logger

from app.rz.models.tagcloud import TagCloudPublic
from app.rz.utils.utils import tagcloud_generator

from app.rz.utils.utils import aliyun_sms_send
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
            detail="生成标签云失败，请稍后重试"
        )
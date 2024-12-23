from fastapi import APIRouter

from fastapi import APIRouter,HTTPException
from app.rz.models.notification import AliyunSMSData
from app.rz.utils.logger import logger

from app.rz.utils.utils import aliyun_sms_send
router = APIRouter(prefix="/utils/notify", tags=["utils"])

@router.post("/aliyun_sms/")
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
        
from pydantic import BaseModel, Field, SecretStr

class AliyunKeyData(BaseModel):
    access_key_id: SecretStr
    access_key_secret: SecretStr

class AliyunSMSData(BaseModel):
    aliyun_key_data: AliyunKeyData
    phone_number: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')  # 使用 Field 函数
    sign_name: str
    template_code: str
    template_param: dict[str, str]

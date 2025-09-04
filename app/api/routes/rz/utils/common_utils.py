import asyncio, hashlib

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, Response

from app.rz.utils.logger import logger
from app.rz.utils.utils import aliyun_sms_send, dns_lookup, generate_static_file, fetch_ipinfo, is_valid_uuid
from app.rz.models.notification import AliyunSMSData

from app.core.config import settings
from pathlib import Path

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
    
@router.get("/resolve", operation_id="resolve_domain")
async def resolve_domain(
    domain: str = Query(..., description="要解析的域名"),
    dns_server: str = Query("8.8.8.8", description="DNS服务器IP"),
    show_ipinfo: bool = Query(False, description="是否查询IP归属地信息")
):
    """
    解析域名并获取其IP地址信息
    - domain: 要解析的域名
    - dns_server: DNS服务器IP地址，默认为 Google 的公共DNS
    - show_ipinfo: 是否查询IP归属地信息，默认为 False
    - Returns:  
        - JSONResponse: 包含域名解析结果和IP归属地信息的JSON响应
    """
    try:
        ipv4_addresses = dns_lookup(domain, "A", dns_server)
        ipv6_addresses = dns_lookup(domain, "AAAA", dns_server)

        ipinfo_results = []
        if show_ipinfo:
            all_ips = ipv4_addresses + ipv6_addresses
            ipinfo_results = await asyncio.gather(
                *[fetch_ipinfo(ip) for ip in all_ips],
                return_exceptions=True
            )
            # 处理异常结果
            ipinfo_results = [
                res if not isinstance(res, Exception) else {"error": str(res)}
                for res in ipinfo_results
            ]
    except Exception as e:
        logger.error(f"域名解析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"域名解析失败: {str(e)}")

    return JSONResponse(content={
        "domain": domain,
        "dns_server": dns_server,
        "ipv4_addresses": ipv4_addresses,
        "ipv6_addresses": ipv6_addresses,
        "ipinfo": ipinfo_results
    })

@router.get("/scripts/tampermonkey/{script_name}")
def view_tampermonkey_script(script_name: str):
    """
    获取Tampermonkey脚本文件
    - script_name: 脚本文件名，格式为 `{UUID}.js`
    - Returns:
        - Response: 返回脚本文件内容，包含适当的缓存头
    该接口会根据请求的脚本名称，动态生成并返回Tampermonkey脚本文件内容。
    仅允许访问以UUID命名且扩展名为`.js`或`.mini.js`的文件
    """
    try:
        file_path = Path(script_name)
        name_part = file_path.stem
        full_suffix = ''.join(file_path.suffixes)
        
        if full_suffix not in ('.js', '.mini.js'):
            raise ValueError
        
        if not is_valid_uuid(name_part):
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid script name format")

    filepath = f"app/rz/templates/tampermonkey/{script_name}"
    try:
        rendered_content = generate_static_file(
            filepath,
            DOMAIN=settings.DOMAIN,
            ENABLELOG=str(settings.LOG_LEVEL == 'DEBUG').lower(),
            API_V1_STR=settings.API_V1_STR
        )
        etag = hashlib.md5(rendered_content.encode('utf-8')).hexdigest()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Script not found")
    except Exception as e:
        logger.error(f"Failed to generate script {script_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate script")

    headers = {
        "Cache-Control": "public, max-age=86400",
        "ETag": f'"{etag}"',
        "Content-Type": "application/javascript; charset=utf-8",
    }

    return Response(rendered_content, media_type='application/javascript', headers=headers)

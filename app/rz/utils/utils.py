import zipfile
import random, string, json, io, uuid
import dns.resolver, httpx

from prometheus_client import Gauge, CollectorRegistry
from jinja2 import Template
from typing import List, Tuple

from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models

from app.rz.models.notification import AliyunSMSData

def performance_data_metrics():
    registry = CollectorRegistry()
    metrics = {
        "frontend_performance": Gauge(
            'latest_frontend_performance', 
            'Latest frontend performance in seconds', 
            ['tracking_domain', 'request_uri'], 
            registry=registry
        ),
        "dns_time": Gauge(
            'latest_dns_time', 
            'Latest DNS time in seconds', 
            ['tracking_domain', 'request_uri'], 
            registry=registry
        ),
        "redirect_time": Gauge(
            'latest_redirect_time', 
            'Latest redirect time in seconds', 
            ['tracking_domain', 'request_uri'], 
            registry=registry
        ),
        "dom_load_time": Gauge(
            'latest_dom_load_time', 
            'Latest DOM load time in seconds', 
            ['tracking_domain', 'request_uri'], 
            registry=registry
        ),
        "ttfb_time": Gauge(
            'latest_ttfb_time', 
            'Latest TTFB time in seconds', 
            ['tracking_domain', 'request_uri'], 
            registry=registry
        ),
        "content_load_time": Gauge(
            'latest_content_load_time', 
            'Latest content load time in seconds', 
            ['tracking_domain', 'request_uri'], 
            registry=registry
        ),
        "onload_callback_time": Gauge(
            'latest_onload_callback_time', 
            'Latest onload callback time in seconds', 
            ['tracking_domain', 'request_uri'], 
            registry=registry
        ),
        "dns_cache_time": Gauge(
            'latest_dns_cache_time', 
            'Latest DNS cache time in seconds', 
            ['tracking_domain', 'request_uri'], 
            registry=registry
        ),
        "unload_time": Gauge(
            'latest_unload_time', 
            'Latest unload time in seconds', 
            ['tracking_domain', 'request_uri'], 
            registry=registry
        ),
        "tcp_handshake_time": Gauge(
            'latest_tcp_handshake_time', 
            'Latest TCP handshake time in seconds', 
            ['tracking_domain', 'request_uri'], 
            registry=registry
        )
    }
    return metrics, registry


def generate_random_string(length=12) -> str:
    """生成一个指定长度的随机字符串"""
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def generate_static_file(filepath: str, **context) -> str:
    """
        通过 Jinja2 模板渲染生成静态文件内容
        - filepath: 模板文件路径
        - context: 模板渲染上下文
        - Returns: 渲染后的内容字符串
    """
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()
    template = Template(content)
    return template.render(**context)


async def aliyun_sms_send(AliyunSMSData: AliyunSMSData) -> dysmsapi_20170525_models.SendSmsResponse:
    """
        发送阿里云短信
    """
    # create client
    config = open_api_models.Config(
        access_key_id=AliyunSMSData.aliyun_key_data.access_key_id.get_secret_value(),
        access_key_secret=AliyunSMSData.aliyun_key_data.access_key_secret.get_secret_value()
    )
    
    config.endpoint = f'dysmsapi.aliyuncs.com'
    
    client = Dysmsapi20170525Client(config)
    
    send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
        phone_numbers=AliyunSMSData.phone_number,
        sign_name=AliyunSMSData.sign_name,
        template_code=AliyunSMSData.template_code,
        template_param=json.dumps(AliyunSMSData.template_param)
    )
    
    runtime = util_models.RuntimeOptions()
    return client.send_sms_with_options(send_sms_request, runtime)

async def create_images_zip(data: List[Tuple[str, bytes]]) -> bytes:
    """创建图像文件的 ZIP 压缩包"""
    if not data:
        raise ValueError("没有图像数据可压缩")
    
    with io.BytesIO() as zip_buffer:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for filename, file_data in data:
                if file_data:  # 确保文件数据不为空
                    zip_file.writestr(filename, file_data)
        return zip_buffer.getvalue()

def dns_lookup(domain: str, record_type: str, dns_server: str, timeout: float = 3.0) -> list[str]:
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_server]
    resolver.timeout = timeout
    resolver.lifetime = timeout
    try:
        answers = resolver.resolve(domain, record_type)
        return [answer.to_text() for answer in answers]
    except (dns.resolver.NXDOMAIN, dns.resolver.Timeout, dns.resolver.NoAnswer, dns.resolver.NoNameservers) as e:
        return []
    
async def fetch_ipinfo(ip: str, timeout: float = 3.0) -> dict:
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(f"https://ipinfo.io/{ip}/json")
            if response.status_code == 200:
                data = response.json()
                data["ip"] = ip
                return data
        except httpx.RequestError as e:
            return {"ip": ip, "error": str(e)}
    return {"ip": ip, "error": "Failed to fetch IPInfo"}

def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False
import tempfile, zipfile
import random, string, json, os, io, uuid
import dns.resolver, httpx
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager

from prometheus_client import Gauge, CollectorRegistry
from jinja2 import Template
from typing import List, Tuple, Dict
from wordcloud import WordCloud
from functools import lru_cache
from pathlib import Path

from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models

from app.rz.models.notification import AliyunSMSData
from app.rz.models.tagcloud import TagCloudPublic

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

@lru_cache(maxsize=None)
def _get_system_fonts_list() -> list:
    """
    获取系统字体列表，并缓存结果。
    """
    return font_manager.findSystemFonts(fontpaths=None, fontext='ttf')

@lru_cache(maxsize=None)
def _get_local_fonts_dict(font_exts: tuple = ('.ttf', '.otf', '.ttc')) -> dict:
    """
    扫描 assets/fonts 目录，将字体文件的文件名（不含扩展名，小写）映射到其完整路径，进行缓存。
    """
    fonts = {}
    local_fonts_dir = Path(__file__).parent.parent / "assets" / "fonts"
    if local_fonts_dir.exists():
        for font_file in local_fonts_dir.rglob("*"):
            if font_file.suffix.lower() in font_exts:
                fonts[font_file.stem.lower()] = str(font_file)
    return fonts

def get_font_path(font_name: str) -> str:
    """
    根据字体名称或路径返回可用字体文件路径，查找顺序：
    1. 直接路径检查
    2. 本地assets/fonts目录
    3. 系统字体目录
    返回匹配的字体路径或第一个系统字体
    
    Args:
        font_name: 字体名称或路径
        
    Returns:
        字体文件完整路径
        
    Raises:
        ValueError: 找不到字体且无系统默认字体
    """
    # 如果是有效路径直接返回
    font_path = Path(font_name)
    if font_path.is_file():
        return str(font_path)
    
    font_name_lower = font_name.lower()
    FONT_EXTS = ('.ttf', '.otf', '.ttc')
    
    # 1. 检查本地字体
    local_fonts = _get_local_fonts_dict(FONT_EXTS)
    if font_name_lower in local_fonts:
        return local_fonts[font_name_lower]
    
    # 2. 检查系统字体
    system_fonts = _get_system_fonts_list()
    for font_path in system_fonts:
        font_stem = Path(font_path).stem.lower()
        # 精确匹配字体名称
        if font_name_lower == font_stem:
            return font_path
    
    # 3. 返回第一个系统字体或报错
    if system_fonts:
        return system_fonts[0]
        
    raise ValueError(f"字体'{font_name}'未找到且无系统默认字体")

async def tagcloud_generator(
    tag_data: TagCloudPublic
) -> str:
    # 准备词频数据
    word_freq: Dict[str, int] = {item.tag: item.count for item in tag_data.tags}
    
    font_path = get_font_path(tag_data.font)
    
    # 配置词云参数
    wordcloud = WordCloud(
        font_path=font_path,
        width=tag_data.width,
        height=tag_data.height,
        background_color=tag_data.background_color
    ).generate_from_frequencies(word_freq)
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(
        prefix='tagcloud_',
        suffix='.png',
        delete=True
    ) as tmp_file:
        file_path = tmp_file.name
    
    # 生成并保存词云图
    plt.figure(figsize=(tag_data.width/100, tag_data.height/100))  # 转换为英寸(100dpi)
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.savefig(file_path, bbox_inches='tight', pad_inches=0, dpi=100)
    plt.close()
    
    return file_path

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
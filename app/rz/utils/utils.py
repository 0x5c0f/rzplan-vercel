from prometheus_client import Gauge, CollectorRegistry

from jinja2 import Template

import random
import string
import json

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

def generate_pcheck_js_file(filepath: str, **context) -> str:
    """
        加载并生成 pcheck.js 文件
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

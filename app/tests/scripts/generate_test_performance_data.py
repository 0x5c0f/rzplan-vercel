import sys
import os

# 添加路径
sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), 
            '..', 
            '..',
            '..'
        )
    )
)

import uuid
import random
import string
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.rz.models.performance_data import PerformanceData  # 确保引入你的模型
from app.rz.models.performance_tracking_config import PerformanceTrackingConfig  # 引入配置模型
from app.core.config import settings  # noqa


def get_url():
    return str(settings.SQLALCHEMY_DATABASE_URI)

def generate_random_string(length=12):
    """生成指定长度的随机字符串"""
    letters = string.ascii_letters + string.digits  # 字母和数字组合
    return ''.join(random.choice(letters) for _ in range(length))

def generate_tracking_config(existing_domains):
    tracking_configs = []
    tracking_domains = [
        "tools.0x5c0f.cc", 
        "blog.0x5c0f.cc"
    ]
    
    # 确保已有的域名也被添加到集合中
    existing_domains.update(tracking_domains)  # 将自定义域名加入现有域名集合

    # 使用自定义域名生成跟踪配置
    for domain in tracking_domains:
        config = PerformanceTrackingConfig(
            id=uuid.uuid4(),
            tracking_domain=domain,  # 使用固定的跟踪域名
            tracking_code=generate_random_string(12),  # 随机生成 12 位的跟踪代码
            is_active=True  # 默认激活状态
        )
        tracking_configs.append(config)

    return tracking_configs

def generate_performance_data(num_records: int, tracking_configs):
    performance_data_list = []
    for _ in range(num_records):
        config = random.choice(tracking_configs)  # 随机选择一个跟踪配置
        data = PerformanceData(
            id=str(uuid.uuid4()),
            dns_time=round(random.uniform(10, 100), 2),
            redirect_time=round(random.uniform(5, 50), 2),
            dom_load_time=round(random.uniform(20, 200), 2),
            frontend_performance=round(random.uniform(100, 500), 2),
            ttfb_time=round(random.uniform(30, 150), 2),
            content_load_time=round(random.uniform(50, 250), 2),
            onload_callback_time=round(random.uniform(10, 100), 2),
            dns_cache_time=round(random.uniform(0, 30), 2),
            unload_time=round(random.uniform(0, 20), 2),
            tcp_handshake_time=round(random.uniform(20, 80), 2),
            request_uri=f"/test/endpoint/{_}",
            tracking_code=config.tracking_code,  # 使用来自跟踪配置的跟踪代码
            tracking_domain=config.tracking_domain,  # 使用来自跟踪配置的跟踪域
            created_at=datetime.now().isoformat()
        )
        performance_data_list.append(data)
    return performance_data_list

def main():
    print(f"Database URI: {get_url()}")
    
    # 创建数据库引擎和会话
    engine = create_engine(get_url())
    Session = sessionmaker(bind=engine)
    session = Session()

    # 检查是否需要插入跟踪配置数据
    tracking_configs = []  # 初始化空列表以保存跟踪配置
    if session.query(PerformanceTrackingConfig).count() == 0:  # 如果表中没有数据
        existing_domains = set()  # 创建一个空集合来存储现有域名
        tracking_configs = generate_tracking_config(existing_domains)
        session.bulk_save_objects(tracking_configs)  # 插入跟踪配置数据
        session.commit()  # 提交事务
        print("跟踪配置数据已成功写入数据库。")
    else:
        print("跟踪配置数据已存在，跳过插入。")
        tracking_configs = session.query(PerformanceTrackingConfig).all()  # 从数据库查询现有配置

    # 生成 30 条测试性能数据
    test_data = generate_performance_data(30, tracking_configs)
    
    # 将性能数据写入数据库
    session.bulk_save_objects(test_data)  # 批量插入
    session.commit()  # 提交事务
    session.close()  # 关闭会话

    print("测试性能数据已成功写入数据库。")

if __name__ == "__main__":
    main()

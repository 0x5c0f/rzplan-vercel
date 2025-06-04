import os
import asyncio
import httpx
import websockets
from uuid import uuid4
from time import time
from pathlib import Path
from app.core.config import settings

from fastapi import UploadFile

from app.rz.utils.logger import logger

class ComfyUIController:
    def __init__(
        self, 
        server_host: str | None = None, 
        server_port: str | None = None
    ):
        host = server_host if server_host is not None else settings.COMFYUI_SERVER_HOST
        port = server_port if server_port is not None else settings.COMFYUI_SERVER_PORT
        self.server_url = f"{host}:{port}"
        # self.server_url = f"{server_host}:{server_port}"
        self.client_id = str(uuid4())
        self.ws = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def connect(self):
        """连接到 ComfyUI WebSocket 服务器"""
        ws_url = f"ws://{self.server_url}/ws?clientId={self.client_id}"
        logger.debug(f"尝试连接: {ws_url}")
        try:
            self.ws = await websockets.connect(ws_url)
            logger.info("WebSocket 连接成功")
            return self.ws
        except Exception as e:
            logger.error(f"WebSocket 连接失败: {e}")
            raise

    async def upload_image_from_path(self, image_file: str = None, is_renamed: bool = True):
        """通过文件路径，上传图片到 ComfyUI 服务器"""
        
        if not os.path.exists(image_file):
            raise FileNotFoundError(f"文件不存在: {image_file}")

        url = f"http://{self.server_url}/upload/image"
        logger.info(f"上传图片: {image_file}")

        # 确定上传时使用的文件名
        if is_renamed:
            # 使用UUID生成随机文件名，保持原始文件扩展名
            original_ext = Path(image_file).suffix
            upload_filename = f"{uuid4()}{original_ext}"
            logger.info(f"使用随机文件名: {upload_filename}")
        else:
            # 使用原始文件名
            upload_filename = os.path.basename(image_file)


        try:
            with open(image_file, "rb") as f:
                files = {'image': (upload_filename, f, 'application/octet-stream')}
                resp = await self.client.post(url, files=files)
                resp.raise_for_status()
                result = resp.json()
                logger.info(f"上传成功，服务器文件名: {result['name']}")
                return result["name"]
        except Exception as e:
            logger.error(f"图片上传失败: {e}")
            raise

    async def upload_image_from_file(self, image_file: UploadFile = None, is_renamed=True):
        """"通过文件对象，上传图片到 ComfyUI 服务器"""

        if image_file is None:
            raise ValueError("image_file 不能为空")

        url = f"http://{self.server_url}/upload/image"
        logger.info(f"上传图片: {image_file.filename}")
        
        # 确定上传时使用的文件名
        if is_renamed:
            original_ext = Path(image_file.filename).suffix if image_file.filename else ''
            upload_filename = f"{uuid4()}{original_ext}"
            logger.info(f"使用随机文件名: {upload_filename}")
        else:
            upload_filename = image_file.filename or f"{uuid4()}"
            
    
        try:
            # 直接上传文件对象
            await image_file.seek(0)
            files = {
                'image': (
                    upload_filename, 
                    image_file.file,
                    image_file.content_type or 'application/octet-stream'
                )
            }
            
            
            # # 先读读取到内存，在上传
            # file_content = await image_file.read()
            
            # files = {
            #     'image': (
            #         upload_filename, 
            #         file_content, 
            #         image_file.content_type or 'application/octet-stream'
            #     )
            # }
            
            resp = await self.client.post(url, files=files)
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"上传成功，服务器文件名: {result['name']}")
            return result["name"]
            
        except Exception as e:
            logger.error(f"图片上传失败: {e}")
            raise


    async def queue_prompt(self, workflow):
        """提交工作流"""
        url = f"http://{self.server_url}/prompt"
        data = {"prompt": workflow, "client_id": self.client_id}

        try:
            resp = await self.client.post(url, json=data)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"工作流提交失败: {e}")
            raise

    async def get_result(self, prompt_id):
        """获取执行结果"""
        if isinstance(prompt_id, dict):
            prompt_id = prompt_id.get("prompt_id", "")

        url = f"http://{self.server_url}/history/{prompt_id}"

        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"获取结果异常: {e}")
            raise

    async def download_images(self, output_data, output_dir="output"):
        """下载输出图片"""
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"下载目录: {os.path.abspath(output_dir)}")

        tasks = []
        for node_id, node_output in output_data.items():
            images = node_output.get("images", [])
            for image in images:
                filename = image["filename"]
                subfolder = image["subfolder"]

                # 路径安全检查
                if ".." in filename or os.path.isabs(filename):
                    logger.warning(f"检测到非法文件名: {filename}")
                    continue

                save_path = os.path.join(output_dir, filename)
                url = f"http://{self.server_url}/view?filename={filename}&subfolder={subfolder}&_={int(time())}"
                tasks.append(self._download_image(url, save_path, node_id))

        await asyncio.gather(*tasks)

    async def _download_image(self, url, save_path, node_id):
        """下载单张图片"""
        try:
            headers = {
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }
            resp = await self.client.get(url, headers=headers)
            resp.raise_for_status()
            with open(save_path, "wb") as f:
                f.write(resp.content)
            logger.debug(f"节点 {node_id}: 下载地址: <{url}>")
            logger.info(f"节点 {node_id}: 下载完成 {save_path} ({len(resp.content)/1024:.1f} KB)")
        except Exception as e:
            logger.error(f"节点 {node_id}: 下载异常: {e}")

    async def close(self):
        """关闭连接和 HTTP 客户端"""
        if self.ws:
            await self.ws.close()
        await self.client.aclose()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

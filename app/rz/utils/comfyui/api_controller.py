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
        """连接到 ComfyUI WebSocket 服务器
        返回:
            WebSocket连接对象
        抛出:
            websockets.exceptions.WebSocketException: 当连接失败时抛出，包含详细错误信息
        """
        ws_url = f"ws://{self.server_url}/ws?clientId={self.client_id}"
        logger.debug(f"尝试连接: {ws_url}")
        try:
            self.ws = await websockets.connect(ws_url)
            logger.info("WebSocket 连接成功")
            return self.ws
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket 连接失败: {e}")
            raise websockets.exceptions.WebSocketException(
                f"无法连接到ComfyUI服务器 {ws_url}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"WebSocket 连接发生意外错误: {e}")
            raise RuntimeError(
                f"连接ComfyUI服务器时发生意外错误: {str(e)}"
            ) from e

    async def upload_image_from_path(self, image_file: str = None, is_renamed: bool = True):
        """通过文件路径，上传图片到 ComfyUI 服务器
        
        参数:
            image_file: 图片文件路径
            is_renamed: 是否重命名文件
            
        返回:
            服务器上的文件名
            
        抛出:
            FileNotFoundError: 当文件不存在时
            httpx.HTTPStatusError: 当HTTP请求失败时
            RuntimeError: 其他意外错误时
        """
        if not image_file:
            raise ValueError("image_file 不能为空")
            
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
        except httpx.HTTPStatusError as e:
            logger.error(f"图片上传HTTP错误: {e}")
            raise httpx.HTTPStatusError(
                f"上传图片到ComfyUI服务器失败 (HTTP {e.response.status_code}): {str(e)}",
                request=e.request,
                response=e.response
            ) from e
        except Exception as e:
            logger.error(f"图片上传发生意外错误: {e}")
            raise RuntimeError(
                f"上传图片时发生意外错误: {str(e)}"
            ) from e

    async def upload_image_from_file(self, image_file: UploadFile = None, is_renamed=True):
        """通过文件对象，上传图片到 ComfyUI 服务器
        
        参数:
            image_file: 上传文件对象
            is_renamed: 是否重命名文件
            
        返回:
            服务器上的文件名
            
        抛出:
            ValueError: 当文件对象为空时
            httpx.HTTPStatusError: 当HTTP请求失败时
            RuntimeError: 其他意外错误时
        """
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
            await image_file.seek(0)
            files = {
                'image': (
                    upload_filename,
                    image_file.file,
                    image_file.content_type or 'application/octet-stream'
                )
            }
            
            resp = await self.client.post(url, files=files)
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"上传成功，服务器文件名: {result['name']}")
            return result["name"]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"图片上传HTTP错误: {e}")
            raise httpx.HTTPStatusError(
                f"上传图片到ComfyUI服务器失败 (HTTP {e.response.status_code}): {str(e)}",
                request=e.request,
                response=e.response
            ) from e
        except Exception as e:
            logger.error(f"图片上传发生意外错误: {e}")
            raise RuntimeError(
                f"上传图片时发生意外错误: {str(e)}"
            ) from e


    async def queue_prompt(self, workflow):
        """提交工作流到ComfyUI服务器
        
        参数:
            workflow: 要提交的工作流数据
            
        返回:
            服务器返回的响应数据
            
        抛出:
            ValueError: 当工作流数据为空时
            httpx.HTTPStatusError: 当HTTP请求失败时
            RuntimeError: 其他意外错误时
        """
        if not workflow:
            raise ValueError("工作流数据不能为空")

        url = f"http://{self.server_url}/prompt"
        data = {"prompt": workflow, "client_id": self.client_id}
        logger.debug(f"提交工作流到: {url}")

        try:
            resp = await self.client.post(url, json=data)
            resp.raise_for_status()
            result = resp.json()
            logger.info("工作流提交成功")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"工作流提交HTTP错误: {e}")
            raise httpx.HTTPStatusError(
                f"提交工作流到ComfyUI服务器失败 (HTTP {e.response.status_code}): {str(e)}",
                request=e.request,
                response=e.response
            ) from e
        except Exception as e:
            logger.error(f"工作流提交发生意外错误: {e}")
            raise RuntimeError(
                f"提交工作流时发生意外错误: {str(e)}"
            ) from e

    async def get_result(self, prompt_id):
        """从ComfyUI服务器获取执行结果
        
        参数:
            prompt_id: 提示ID，可以是字符串或包含prompt_id的字典
            
        返回:
            服务器返回的结果数据
            
        抛出:
            ValueError: 当prompt_id无效时
            httpx.HTTPStatusError: 当HTTP请求失败时
            RuntimeError: 其他意外错误时
        """
        if not prompt_id:
            raise ValueError("prompt_id不能为空")

        if isinstance(prompt_id, dict):
            prompt_id = prompt_id.get("prompt_id", "")
            if not prompt_id:
                raise ValueError("字典中缺少有效的prompt_id")

        url = f"http://{self.server_url}/history/{prompt_id}"
        logger.debug(f"获取执行结果: {url}")

        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            result = resp.json()
            logger.info("成功获取执行结果")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"获取结果HTTP错误: {e}")
            raise httpx.HTTPStatusError(
                f"从ComfyUI服务器获取结果失败 (HTTP {e.response.status_code}): {str(e)}",
                request=e.request,
                response=e.response
            ) from e
        except Exception as e:
            logger.error(f"获取结果发生意外错误: {e}")
            raise RuntimeError(
                f"获取执行结果时发生意外错误: {str(e)}"
            ) from e

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

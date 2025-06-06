import asyncio
import io
from fastapi import APIRouter,HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Dict
from app.rz.utils.logger import logger
from app.rz.utils.utils import tagcloud_generator, aliyun_sms_send
from app.rz.utils.comfyui.api_controller import ComfyUIController
from app.rz.utils.comfyui.workflow_controller import WorkflowController
from app.rz.crud.comfyui_controller import upload_images_to_comfyui, parse_workflow_data, parse_server_info

from app.rz.models.notification import AliyunSMSData
from app.rz.models.tagcloud import TagCloudPublic
from app.rz.models.comfyui_workflow import WorkFlowNodePublic, ComfyUITaskPublic, WorkFlowImageUploadPublic

from app.rz.utils.utils import create_images_zip

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
            detail=f"生成标签云失败: {str(e)}"
        )

@router.post("/comfyui/upload-image")
async def upload_image_to_comfyui(
    comfyui_server: WorkFlowImageUploadPublic = Depends(parse_server_info),
    images: List[UploadFile] = File(),
) -> Dict:
    """上传图片到comfyui input 目录，返回上传后的文件名与原文件名的对应关系"""
    
    # 构建服务器URL
    comfyui_controller = ComfyUIController(comfyui_server.server_info.server_host, comfyui_server.server_info.server_port)
    
    try:
        async with comfyui_controller:
            upload_result = await upload_images_to_comfyui(images, comfyui_controller)
            
            return {
                "success": True,
                "message": f"Processed {len(images)} images",
                "server_url": comfyui_controller.server_url,
                "file_mapping": upload_result["file_mapping"],
                "upload_details": upload_result["upload_details"]
            }
            
    except HTTPException:
        raise  # 直接抛出已有的HTTP异常
    except Exception as e:
        logger.error(f"Error during upload process: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        await comfyui_controller.close()
        

@router.post("/comfyui/workflow/queue")
async def workflow_queue(
    data_in: WorkFlowNodePublic = Depends(parse_workflow_data),
    workflow_file: UploadFile = File(...),
) -> Dict:
    """
    创建工作流队列，并返回结果
    - **workflow**: 工作流文件
    - **data_in**:  待修改工作流数据，例如：
      ```json
        {
            "server_info": { // 此项可选，默认使用系统配置文件中的信息
                "server_host": "172.16.110.240",
                "server_port": "8189"
            },
            "node_info": [
                {
                    "node_id": 0,
                    "inputs": [
                        {
                        "node_input_key": "images",
                        "node_input_value": "bd7d2c0e-4ab0-4639-bfd6-d55a0f0cf3ec.jpg"
                        }
                    ]
                }
            ]
        }
      ```
    """
    
    workflowController = WorkflowController(workflow_file)
    workflow = {}
    try:
        async with workflowController:
            node_info = data_in.node_info
            for node in node_info:
                workflow = await workflowController.update_node_input(node)

            server_info = data_in.server_info
            comfyui_controller = ComfyUIController(server_info.server_host, server_info.server_port)

            try:
                async with comfyui_controller:
                    queue_response = await comfyui_controller.queue_prompt(workflow)
                    prompt_id = queue_response.get("prompt_id")
                    logger.info(f"任务排队ID: {prompt_id}")

                # 返回任务ID
                return {
                    "messgae": "任务提交成功",
                    "task_id": f"{prompt_id}"
                }
                
                # # 获取结果
                # while True:
                #     try:
                #         result = await comfyui_controller.get_result(prompt_id)
                #     except Exception as e:
                #         logger.error(f"获取结果时出错: {str(e)}")
                #         await asyncio.sleep(1)
                #         continue
                #     if prompt_id in result:
                #         await comfyui_controller.download_images(result[prompt_id]["outputs"])
                #         break
                #     await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"ComfyUI操作失败: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"ComfyUI操作失败: {str(e)}"
                )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Workflow processing failed: {str(e)}"
        )

@router.post("/comfyui/workflow/task")
async def workflow_task(
    data_in: ComfyUITaskPublic
):
    """
    查询任务{task_id}，并返回执行结果
    Args:
    - data_in: 包含任务ID的输入数据, 例如:
        ```json
        {
            "task_id": "015fe59e-6fba-4f61-8ea3-1efdf1c18366",
            "server_info": { // 此项可选，默认使用系统配置文件中的信息
                "server_host": "127.0.0.1",
                "server_port": "8188"
            }
        }
        ```
    
    
    Returns:
    - StreamingResponse: 包含所有生成图像的 ZIP 文件(只会下载 class_type = SaveImage 节点生成的图像)
    - HTTPException: 如果发生错误，将返回 HTTPException
    """
    
    comfyui_controller = ComfyUIController(data_in.server_info.server_host, data_in.server_info.server_port)

    prompt_id = str(data_in.task_id)

    try:
        async with comfyui_controller:
            result = await comfyui_controller.get_result(prompt_id)
            if not result:
                raise HTTPException(
                    status_code=404,
                    detail=f"任务 {prompt_id} 的结果为空，可能尚未完成或不存在"
                )
            
            if prompt_id in result:
                workflow_controller = WorkflowController(result)
                async with workflow_controller:
                    image_files = await workflow_controller.extract_image_files()
                    logger.info(f"待保存图像文件列表: {image_files}")

                    # 下载指定文件名的图片
                    output_images = await comfyui_controller.download_images_as_stream(image_files)
                    if not output_images:
                        raise HTTPException(
                            status_code=404,
                            detail="没有查询到任务结果，该任务可能未完成，请稍后在查询"
                        )
            
                zip_data = await create_images_zip(output_images)
                
                # 返回zip文件
                return StreamingResponse(
                    io.BytesIO(zip_data),
                    media_type="application/zip",
                    headers={
                        "Content-Disposition": f"attachment; filename=comfyui_output_{prompt_id}.zip",
                        "Content-Length": str(len(zip_data)),
                        "Content-Type": "application/zip"
                    }
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="没有查询到任务结果，该任务可能未完成，请稍后在查询"
                )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"{str(e)}"
        )
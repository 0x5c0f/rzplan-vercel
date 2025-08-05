import io
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import StreamingResponse

from app.rz.utils.comfyui.api_controller import ComfyUIController
from app.rz.utils.comfyui.workflow_controller import WorkflowController
from app.rz.crud.comfyui_controller import upload_images_to_comfyui, parse_workflow_data, parse_server_info

from app.rz.models.comfyui_workflow import WorkFlowNodePublic, ComfyUITaskPublic, WorkFlowImageUploadPublic

from typing import List, Dict

from app.rz.utils.utils import create_images_zip

from app.rz.utils.logger import logger

router = APIRouter(prefix="/utils", tags=["utils"])


@router.post("/comfyui/upload-image")
async def upload_image_to_comfyui(
    comfyui_server: WorkFlowImageUploadPublic = Depends(parse_server_info),
    images: List[UploadFile] = File(),
) -> Dict:
    """
    上传图片到comfyui input 目录
    Args:
    - server_info: comfyui 服务器信息, 例如
        ```json
        {
            "server_info": { // 此项可选，默认使用系统配置文件中的信息
                "server_host": "127.0.0.1",
                "server_port": "8188"
            }
        }
        ```    
    - images: 上传的图片对象
    
    Returns:
    - Dict: 上传后的文件名与原文件名的对应关系
    """
    
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
                "server_host": "127.0.0.1",
                "server_port": "8188"
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
                    task = await comfyui_controller.get_result(prompt_id) 
                    logger.info(f"task = {task}")
                    order = 0
                    if 'data' in task and 'order'in task['data']:
                        order = task['data']['order']

                # 返回任务ID
                return {
                    "messgae": "任务提交成功",
                    "task_id": f"{prompt_id}",
                    "order": order
                }
                
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
    - StreamingResponse: 如果工作流只生成了一张图片，直接返回图片对象，如果有多张图片，返回ZIP 文件
        - 只会下载 class_type = SaveImage/SaveImagePlus 节点生成的图像    
    - json: 任务未完成， 返回排序号 = 'order'；order = 0代表任务正在运行中，order > 0 代表等待中
        - success=False时代表处理出错， 见errMessage
        ```json
        {
            'success': True, 
            'errMessage': '', 
            'data': {
                'order': 3
            } 
        }
        ```    
    
    - HTTPException: 如果发生错误，将返回 HTTPException
    """
    
    comfyui_controller = ComfyUIController(data_in.server_info.server_host, data_in.server_info.server_port)

    prompt_id = str(data_in.task_id)

    try:
        async with comfyui_controller:
            result = await comfyui_controller.get_result(prompt_id) 
            
            #处理失败或任务未完成
            if 'success' in result:
                return result
            
            # 任务已经开始结束
            if prompt_id in result:
                workflow_controller = WorkflowController(result)
                async with workflow_controller:
                    image_files = await workflow_controller.extract_image_files()
                    logger.info(f"待保存图像文件列表: {image_files}")
                    
                    if not image_files:
                        raise HTTPException(
                            status_code=404,
                            detail="任务处理失败，未生成结果。"
                        )

                    # 下载指定文件名的图片
                    output_images = await comfyui_controller.download_images_as_stream(image_files)
                    if not output_images:
                        raise HTTPException(
                            status_code=404,
                            detail="图片下载失败，可能临时图片已被清理。"
                        )

                    if len(output_images) == 1: # 单张图片直接返回                       
                        image_name, image_data = output_images[0]    
                        file_extension = image_name.lower().split('.')[-1]
                        media_type_map = {
                            'png': 'image/png',
                            'jpg': 'image/jpeg',
                            'jpeg': 'image/jpeg',
                            'gif': 'image/gif',
                            'webp': 'image/webp',
                            'bmp': 'image/bmp',
                            'webm': 'video/webm',
                            'mp4': 'video/mp4'
                        }
                        media_type = media_type_map.get(file_extension, 'image/webp')                        
                        return StreamingResponse(
                            io.BytesIO(image_data),
                            media_type=media_type,
                            headers={
                                "Content-Disposition": f"attachment; filename={image_name}",
                                "Content-Length": str(len(image_data)),
                                "Content-Type": media_type
                            }
                        )
                    else: # 多张图片返回压缩文件                       
                        zip_data = await create_images_zip(output_images)                        
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
                    detail="没有查询到该任务1"
                )
    except LookupError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={str(e)}
        )

@router.post("/comfyui/query/train")
async def workflow_query_train(lora_name: str) -> dict:
    """
    查询指定 LoRA 模型的训练状态，并以 JSON 对象形式返回结果。
    Args:
    - lora_name: 正在训练的 LoRA 模型名称。

    Returns:
    - dict: 包含训练状态的字典。
    - HTTPException: 如果发生错误或未找到状态文件，则返回 HTTP 异常。
    """
    import os,json
    from app.core.config import settings
    dataset_dir = settings.COMFYUI_CACHE_DIR
    task_status_file = f"{dataset_dir}/{lora_name}/status.json"

    # 检查状态文件是否存在
    if not os.path.exists(task_status_file):
        raise HTTPException(status_code=404, detail=f"LoRA '{lora_name}' 的状态文件未找到。")

    try:
        with open(task_status_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data 
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"解析 '{lora_name}' 状态文件中的 JSON 时出错。")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发生意外错误: {e}")
    

@router.post("/comfyui/queue/move_first")
async def workflow_move_first(
        data_in: ComfyUITaskPublic
    ):
    """
    将指定的任务 提高优先级， 放在正在执行的任务的下一个。 
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
    - json, success=True代表重排序成功， 为False时处理失败， 原因见 errMessage
        ```json
        {
            "success":false,
            "errMessage":"队列为空，无需处理",
            "data":{}
        }
        ```
        
    - HTTPException: 如果发生错误或未找到状态文件，则返回 HTTP 异常。
    """    
    import json
    comfyui_controller = ComfyUIController(data_in.server_info.server_host, data_in.server_info.server_port)

    prompt_id = str(data_in.task_id)

    try:
        async with comfyui_controller:
            return await comfyui_controller.move_to_front(prompt_id)  
        return False 
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"JSON格式不正确。")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发生意外错误: {e}") 

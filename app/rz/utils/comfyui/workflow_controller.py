import json
from typing import Any, Dict, Optional, List, Union
from fastapi import UploadFile

from app.rz.models.comfyui_workflow import WorkFlowNodeInputs
from app.rz.utils.logger import logger

class WorkflowController:
    def __init__(self, workflow_file: Optional[Union[UploadFile, Dict[str, Any]]] = None):
        self.workflow_file = workflow_file if isinstance(workflow_file, UploadFile) else None
        self.workflow: Dict[str, Any] = workflow_file if isinstance(workflow_file, dict) else {}

    async def update_node_input(self, node_info: WorkFlowNodeInputs | None = None):
        if node_info is None:
            error_msg = "工作流节点信息为空"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        node_id = str(node_info.node_id)
        logger.debug(f"当前修改节点 {node_id}, 工作流: {self.workflow}")
        if node_id not in self.workflow:
            error_msg = f"工作流节点 {node_id} 不存在"
            logger.error(error_msg)
            raise KeyError(error_msg)
            
        # 更新节点输入
        for input_item in node_info.inputs:
            self.workflow[node_id]['inputs'][input_item.node_input_key] = input_item.node_input_value
            
        return self.workflow
        # return json.dumps(self.workflow,ensure_ascii=False)


    def get_nodes(self) -> List[str]:
        """获取所有节点ID列表"""
        return list(self.workflow.keys())

    def get_node(self, node_id: str) -> Optional[Dict]:
        """获取指定节点数据"""
        return self.workflow.get(node_id)

    def get_node_input(self, node_id: str, input_key: str) -> Any:
        """获取节点的特定输入参数"""
        if node_id not in self.workflow:
            print(f"❌ 节点 {node_id} 不存在")
            return None
        
        return self.workflow[node_id].get('inputs', {}).get(input_key)

    def get_node_inputs(self, node_id: str) -> Dict[str, Any]:
        """获取节点的所有输入参数"""
        if node_id not in self.workflow:
            print(f"❌ 节点 {node_id} 不存在")
            return {}
        
        return self.workflow[node_id].get('inputs', {})

    def find_nodes_by_class(self, class_type: str) -> List[str]:
        """根据类型查找节点"""
        return [node_id for node_id, node_data in self.workflow.items()
                if node_data.get('class_type') == class_type]

    def find_save_images_node_id_by_classtype(self, class_type: str) -> List[str]:
        """专门处理ComfyUI格式工作流，根据类型查找节点"""
        if not isinstance(self.workflow, dict):
            return []
            
        save_image_nodes = {}
        
        def search_for_nodes(current_data):
            if isinstance(current_data, dict):
                for key, value in current_data.items():
                    if isinstance(value, dict) and value.get("class_type") == class_type:
                        save_image_nodes[key] = value
                    else:
                        search_for_nodes(value)
            elif isinstance(current_data, list):
                for item in current_data:
                    search_for_nodes(item)

        search_for_nodes(self.workflow)
        logger.info("Found nodes: %s", save_image_nodes)
        return list(save_image_nodes.keys())
        # # 如果是标准ComfyUI格式
        # if "prompt" in self.workflow and isinstance(self.workflow["prompt"], list) and len(self.workflow["prompt"]) > 1:
        #     nodes = self.workflow["prompt"][1]
        #     return [node_id for node_id, node_data in nodes.items()
        #            if isinstance(node_data, dict) and node_data.get('class_type') == class_type]
        
        # # 默认行为
        # return self.find_nodes_by_class(class_type)

    async def extract_image_files(self) -> List[str]:
        """提取工作流中所有输出图像文件名
        
        Returns:
            List[str]: 图像文件名列表
        """
        image_files = []
        save_images_node_id = self.find_save_images_node_id_by_classtype("SaveImage")
        for image_id in save_images_node_id:
            logger.info(f"获取到保存图像的节点id: {image_id}")
            output_node = self.find_output_images_node_by_save_images_node_id(image_id)
            logger.info(f"获取到图像保存结果节点信息: {output_node}")
            for image_info in output_node.get('images', []):
                image_files.append(image_info['filename'])
        return image_files
    
    def find_output_images_node_by_save_images_node_id(self, save_image_id: str):
        """根据保存图片ID查找输出图片节点"""
        outputs_section = None
        for key, value in self.workflow.items():
            if isinstance(value, dict) and "outputs" in value:
                outputs_section = value.get("outputs")
                break # Assuming only one 'outputs' section at this level

        if outputs_section and save_image_id in outputs_section:
            return outputs_section[save_image_id]
        else:
            return None
        
    def find_nodes_by_input_key(self, input_key: str) -> List[str]:
        """根据输入参数键查找节点"""
        return [node_id for node_id, node_data in self.workflow.items() 
                if input_key in node_data.get('inputs', {})]
    
    def find_nodes_by_input_value(self, input_key: str, value: Any) -> List[str]:
        """根据输入参数值查找节点"""
        return [node_id for node_id, node_data in self.workflow.items() 
                if node_data.get('inputs', {}).get(input_key) == value]

    def get_node_connections(self, node_id: str) -> Dict[str, List[str]]:
        """获取节点的连接关系"""
        if node_id not in self.workflow:
            return {'inputs': [], 'outputs': []}
        
        inputs = []
        outputs = []
        
        # 查找输入连接
        node_inputs = self.workflow[node_id].get('inputs', {})
        for key, value in node_inputs.items():
            if isinstance(value, list) and len(value) == 2:
                if isinstance(value[0], str) and value[0] in self.workflow:
                    inputs.append(f"{value[0]}[{value[1]}] -> {key}")
        
        # 查找输出连接
        for other_id, other_data in self.workflow.items():
            if other_id == node_id:
                continue
            other_inputs = other_data.get('inputs', {})
            for key, value in other_inputs.items():
                if isinstance(value, list) and len(value) == 2:
                    if value[0] == node_id:
                        outputs.append(f"{key} -> {other_id}[{value[1]}]")
        
        return {'inputs': inputs, 'outputs': outputs}
    
    def validate_workflow(self) -> Dict[str, List[str]]:
        """验证工作流的完整性"""
        errors = []
        warnings = []
        
        for node_id, node_data in self.workflow.items():
            # 检查必需字段
            if 'class_type' not in node_data:
                errors.append(f"节点 {node_id} 缺少 class_type")
            
            if 'inputs' not in node_data:
                warnings.append(f"节点 {node_id} 缺少 inputs")
                continue
            
            # 检查连接的有效性
            inputs = node_data['inputs']
            for input_key, input_value in inputs.items():
                if isinstance(input_value, list) and len(input_value) == 2:
                    target_node = input_value[0]
                    if isinstance(target_node, str) and target_node not in self.workflow:
                        errors.append(f"节点 {node_id} 的输入 {input_key} 引用了不存在的节点 {target_node}")
        
        return {'errors': errors, 'warnings': warnings}

    async def __aenter__(self):
        """异步上下文管理器入口，加载工作流文件"""
        if isinstance(self.workflow_file, UploadFile):
            try:
                content = await self.workflow_file.read()
                self.workflow = json.loads(content)
                await self.workflow_file.seek(0)
            except json.JSONDecodeError as e:
                logger.error(f"工作流JSON解析失败: {str(e)}")
                raise ValueError("无效的工作流JSON格式") from e
            except Exception as e:
                logger.error(f"工作流加载异常: {str(e)}")
                raise
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口，确保文件资源被释放"""
        if self.workflow_file:
            try:
                await self.workflow_file.close()
            except Exception as e:
                logger.warning(f"文件关闭异常: {str(e)}")

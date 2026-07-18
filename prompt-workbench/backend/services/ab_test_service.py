import sys  # 系统模块（系统）
import os  # 文件系统（文件系统）

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx  # HTTP客户端（HTTP客户端）
import asyncio  # 异步IO（异步）

class ABTestService:
    """A/B测试服务（A/B测试服务）- 使用同一模型对比不同Prompt"""
    async def run_ab_test(self, db, version_a_id: int, version_b_id: int, 
                          test_input: str, model_config_id: int = None) -> dict:
        """运行A/B测试（运行A/B测试）"""
        from database.crud import get_model_config, get_default_model_config, get_prompt_version  # 导入CRUD（导入CRUD）
        from utils.encryption import decrypt_api_key  # 导入解密工具（导入解密）
        
        version_a = get_prompt_version(db, version_a_id)  # 获取版本A（获取版本A）
        version_b = get_prompt_version(db, version_b_id)  # 获取版本B（获取版本B）
        
        if not version_a or not version_b:
            return {"error": "版本不存在"}  # 返回错误（错误）
        
        # 获取模型配置（获取模型配置）
        if model_config_id:
            config = get_model_config(db, model_config_id)  # 指定配置（指定配置）
        else:
            config = get_default_model_config(db)  # 默认配置（默认配置）
        
        if not config:
            return {"error": "未配置模型"}  # 返回错误（错误）
        
        # 填充测试输入（填充输入）
        prompt_a = version_a.content.replace("{{input}}", test_input)  # 替换输入变量（替换）
        prompt_b = version_b.content.replace("{{input}}", test_input)  # 替换输入变量（替换）
        
        api_key = decrypt_api_key(config.api_key)  # 解密API密钥（解密密钥）
        
        async def call_api(prompt):
            """调用API（调用API）"""
            try:
                async with httpx.AsyncClient(timeout=60) as client:  # 创建HTTP客户端（创建客户端）
                    response = await client.post(
                        f"{config.api_base}/chat/completions",  # API端点（API端点）
                        headers={
                            "Content-Type": "application/json",  # 内容类型（内容类型）
                            "Authorization": f"Bearer {api_key}"  # 授权头（授权头）
                        },
                        json={
                            "model": config.model_id,  # 模型ID（模型ID）
                            "messages": [
                                {"role": "user", "content": prompt}  # 用户消息（用户消息）
                            ],
                            "temperature": 0.7  # 温度参数（温度）
                        }
                    )
                    
                    if response.status_code == 200:  # 检查响应（检查响应）
                        result = response.json()  # 解析JSON（解析）
                        return result["choices"][0]["message"]["content"]  # 返回内容（返回内容）
                    else:
                        return f"API Error: {response.status_code}"  # 返回错误（错误）
            except Exception as e:
                return f"Error: {str(e)}"  # 返回异常（异常）
        
        # 并行调用（并行调用）
        task_a = asyncio.create_task(call_api(prompt_a))  # 创建任务A（任务A）
        task_b = asyncio.create_task(call_api(prompt_b))  # 创建任务B（任务B）
        
        output_a, output_b = await asyncio.gather(task_a, task_b)  # 并行执行（并行执行）
        
        return {
            "output_a": output_a,  # 输出A（输出A）
            "output_b": output_b,  # 输出B（输出B）
            "version_a_id": version_a_id,  # 版本A（版本A）
            "version_b_id": version_b_id,  # 版本B（版本B）
            "test_input": test_input  # 测试输入（测试输入）
        }
    
    def format_prompt(self, prompt_content: str, variables: dict) -> str:
        """格式化Prompt（格式化提示词）"""
        result = prompt_content  # 初始结果（初始）
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", value)  # 替换{{{key}}}（替换）
            result = result.replace(f"[{key}]", value)  # 替换[key]（替换）
            result = result.replace(f"{{{key}}}", value)  # 替换{key}（替换）
        return result  # 返回结果（返回）

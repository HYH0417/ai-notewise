import numpy as np  # 数值计算库（数值计算）
import os  # 文件系统（文件系统）
import json  # JSON处理（JSON处理）

class ChromaService:
    """向量存储服务（向量存储服务）- 自定义实现，替代ChromaDB"""
    def __init__(self):
        self.vectors = {}  # 向量字典（向量）
        self.documents = {}  # 文档字典（文档）
        self.metadatas = {}  # 元数据字典（元数据）
        self.persist_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            "vector_db",
        )  # 持久化目录（持久化目录）
        os.makedirs(self.persist_dir, exist_ok=True)  # 创建目录（创建目录）
        self._load_from_disk()  # 从磁盘加载（加载数据）
    
    def _save_to_disk(self):
        """保存到磁盘（保存到磁盘）"""
        data = {
            "vectors": {str(k): v.tolist() for k, v in self.vectors.items()},  # 向量转列表（向量数据）
            "documents": self.documents,  # 文档数据（文档数据）
            "metadatas": self.metadatas  # 元数据（元数据）
        }
        with open(os.path.join(self.persist_dir, "vectors.json"), "w", encoding="utf-8") as f:
            json.dump(data, f)  # 写入JSON文件（写入文件）
    
    def _load_from_disk(self):
        """从磁盘加载（从磁盘加载）"""
        file_path = os.path.join(self.persist_dir, "vectors.json")  # 文件路径（文件路径）
        if os.path.exists(file_path):  # 检查文件存在（检查存在）
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)  # 读取JSON（读取）
                    self.vectors = {int(k): np.array(v) for k, v in data.get("vectors", {}).items()}  # 向量恢复（向量恢复）
                    self.documents = {int(k): v for k, v in data.get("documents", {}).items()}  # 文档恢复（文档恢复）
                    self.metadatas = {int(k): v for k, v in data.get("metadatas", {}).items()}  # 元数据恢复（元数据恢复）
            except:
                pass  # 异常处理（异常处理）
    
    def add_prompt(self, prompt_id: int, content: str, embedding: np.ndarray):
        """添加Prompt到向量存储（添加提示词）"""
        self.vectors[prompt_id] = embedding  # 存储向量（存储向量）
        self.documents[prompt_id] = content  # 存储文档（存储文档）
        self.metadatas[prompt_id] = {"prompt_id": prompt_id}  # 存储元数据（存储元数据）
        self._save_to_disk()  # 保存到磁盘（保存）
    
    def delete_prompt(self, prompt_id: int):
        """从向量存储删除Prompt（删除提示词）"""
        if prompt_id in self.vectors:  # 检查存在（检查存在）
            del self.vectors[prompt_id]  # 删除向量（删除向量）
            del self.documents[prompt_id]  # 删除文档（删除文档）
            del self.metadatas[prompt_id]  # 删除元数据（删除元数据）
            self._save_to_disk()  # 保存到磁盘（保存）
    
    def search(self, query: str, embedding: np.ndarray, top_k: int = 10, 
               scenario: str = None, tags: list = None) -> list:
        """向量检索（向量检索）"""
        if not self.vectors:  # 检查是否有数据（检查数据）
            return []  # 返回空列表（空列表）
        
        prompt_ids = list(self.vectors.keys())  # 获取所有ID（获取ID）
        all_vectors = np.array([self.vectors[p_id] for p_id in prompt_ids])  # 转换为数组（转换数组）
        
        embedding = embedding.reshape(1, -1)  # 重塑维度（重塑维度）
        similarities = np.dot(all_vectors, embedding.T).flatten()  # 计算余弦相似度（计算相似度）
        similarities = (similarities + 1) / 2  # 归一化到[0,1]（归一化）
        
        results = []  # 结果列表（结果）
        for i, p_id in enumerate(prompt_ids):
            results.append({
                "prompt_id": p_id,  # PromptID（提示词ID）
                "document": self.documents[p_id],  # 文档内容（文档）
                "similarity": float(similarities[i])  # 相似度（相似度）
            })
        
        results.sort(key=lambda x: x["similarity"], reverse=True)  # 按相似度排序（排序）
        
        return results[:top_k]  # 返回前k个（返回）
    
    def update_prompt(self, prompt_id: int, content: str, embedding: np.ndarray):
        """更新Prompt的向量（更新提示词）"""
        self.delete_prompt(prompt_id)  # 删除旧数据（删除旧数据）
        self.add_prompt(prompt_id, content, embedding)  # 添加新数据（添加新数据）
    
    def get_all_prompts(self) -> list:
        """获取所有Prompt（获取所有提示词）"""
        return [
            {
                "prompt_id": p_id,  # PromptID（提示词ID）
                "document": self.documents[p_id],  # 文档内容（文档）
                "metadata": self.metadatas[p_id]  # 元数据（元数据）
            }
            for p_id in self.vectors.keys()  # 遍历所有ID（遍历）
        ]
    
    def get_prompt(self, prompt_id: int) -> dict:
        """获取单个Prompt（获取提示词）"""
        if prompt_id in self.vectors:  # 检查存在（检查存在）
            return {
                "prompt_id": prompt_id,  # PromptID（提示词ID）
                "document": self.documents[prompt_id],  # 文档内容（文档）
                "metadata": self.metadatas[prompt_id]  # 元数据（元数据）
            }
        return None  # 不存在返回None（不存在）

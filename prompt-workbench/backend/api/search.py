import sys  # 系统模块（系统）
import os  # 文件系统（文件系统）

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException  # FastAPI组件（FastAPI）
from sqlalchemy.orm import Session  # 数据库会话（会话）
from database import get_db  # 获取数据库会话（获取会话）
from database.crud import get_prompt, chroma_service, embedding_service  # CRUD函数和共享服务实例（CRUD和服务）
from schemas import SearchRequest, SearchResult  # 数据模型（数据模型）

# 创建路由实例（创建路由）
router = APIRouter(prefix="/search", tags=["search"])  # 前缀/search，标签search（路由）

@router.post("/", response_model=list[SearchResult])
def semantic_search(request: SearchRequest, db: Session = Depends(get_db)):
    """语义搜索（语义搜索）- POST方式"""
    embedding = embedding_service.encode(request.query)  # 编码查询词（编码）
    
    results = chroma_service.search(
        query=request.query,
        embedding=embedding,
        top_k=request.top_k,
        scenario=request.scenario,
        tags=request.tags
    )  # 向量检索（检索）
    
    search_results = []  # 结果列表（结果）
    for result in results:
        prompt = get_prompt(db, result["prompt_id"])  # 获取Prompt（获取）
        if prompt:
            search_results.append(SearchResult(
                prompt_id=prompt.id,
                title=prompt.title,
                scenario=prompt.scenario,
                similarity=round(result["similarity"], 4),
                content=result["document"]
            ))  # 构建结果（构建）
    
    return search_results

@router.get("/simple")
def search_get(query: str, scenario: str = None, tags: str = None, 
               top_k: int = 10, db: Session = Depends(get_db)):
    """简单搜索（简单搜索）- GET方式"""
    embedding = embedding_service.encode(query)  # 编码查询词（编码）
    
    tag_list = tags.split(",") if tags else None  # 解析标签（解析标签）
    
    results = chroma_service.search(
        query=query,
        embedding=embedding,
        top_k=top_k,
        scenario=scenario,
        tags=tag_list
    )  # 向量检索（检索）
    
    search_results = []  # 结果列表（结果）
    for result in results:
        prompt = get_prompt(db, result["prompt_id"])  # 获取Prompt（获取）
        if prompt:
            search_results.append({
                "prompt_id": prompt.id,
                "title": prompt.title,
                "scenario": prompt.scenario,
                "similarity": round(result["similarity"], 4),
                "content": result["document"]
            })  # 构建结果（构建）
    
    return search_results

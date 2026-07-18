import sys  # 系统模块（系统）
import os  # 文件系统（文件系统）

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException  # FastAPI组件（FastAPI）
from sqlalchemy.orm import Session  # 数据库会话（会话）
from database import get_db  # 获取数据库会话（获取会话）
from database.crud import (
    create_ab_test, update_ab_test, get_ab_test, get_ab_tests  # CRUD函数（CRUD）
)
from schemas import ABTestCreate, ABTestUpdate, ABTestResponse  # 数据模型（数据模型）
from services.ab_test_service import ABTestService  # A/B测试服务（A/B测试）

# 创建路由实例（创建路由）
router = APIRouter(prefix="/ab-test", tags=["ab-test"])  # 前缀/ab-test，标签ab-test（路由）
ab_test_service = ABTestService()  # A/B测试实例（A/B测试）

@router.post("/", response_model=ABTestResponse)
async def run_ab_test_endpoint(request: ABTestCreate, db: Session = Depends(get_db)):
    """运行A/B测试（运行A/B测试）"""
    result = await ab_test_service.run_ab_test(
        db,
        version_a_id=request.version_a_id,
        version_b_id=request.version_b_id,
        test_input=request.test_input,
        model_config_id=request.model_config_id
    )  # 运行测试（运行测试）
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])  # 抛出错误（错误）
    
    ab_test = create_ab_test(
        db,
        test_input=request.test_input,
        version_a_id=request.version_a_id,
        version_b_id=request.version_b_id,
        output_a=result["output_a"],
        output_b=result["output_b"]
    )  # 创建测试记录（创建记录）
    
    return ab_test

@router.get("/", response_model=list[ABTestResponse])
def list_ab_tests(prompt_id: int = None, skip: int = 0, limit: int = 100, 
                  db: Session = Depends(get_db)):
    """获取A/B测试列表（获取测试列表）"""
    return get_ab_tests(db, prompt_id=prompt_id, skip=skip, limit=limit)

@router.get("/{test_id}", response_model=ABTestResponse)
def get_ab_test_detail(test_id: int, db: Session = Depends(get_db)):
    """获取A/B测试详情（获取测试详情）"""
    ab_test = get_ab_test(db, test_id)  # 获取测试（获取）
    if not ab_test:
        raise HTTPException(status_code=404, detail="AB Test not found")  # 抛出404（未找到）
    return ab_test

@router.put("/{test_id}", response_model=ABTestResponse)
def update_ab_test_result(test_id: int, request: ABTestUpdate, db: Session = Depends(get_db)):
    """更新A/B测试结果（更新测试结果）"""
    ab_test = update_ab_test(db, test_id, **request.dict(exclude_unset=True))  # 更新（更新）
    if not ab_test:
        raise HTTPException(status_code=404, detail="AB Test not found")  # 抛出404（未找到）
    return ab_test

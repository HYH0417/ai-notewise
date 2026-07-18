import sys  # 系统模块（系统）
import os  # 文件系统（文件系统）

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException  # FastAPI组件（FastAPI）
from sqlalchemy.orm import Session  # 数据库会话（会话）
from database import get_db  # 获取数据库会话（获取会话）
from database.crud import (
    create_model_config, get_model_config, get_model_configs,
    get_default_model_config, update_model_config, delete_model_config  # CRUD函数（CRUD）
)
from schemas import ModelConfigCreate, ModelConfigUpdate, ModelConfigResponse  # 数据模型（数据模型）
from services.pattern_recognition import PatternRecognition  # 模式识别服务（模式识别）
from schemas import PatternDetectionRequest, PatternDetectionResponse  # 模式检测模型（模式检测）

# 创建路由实例（创建路由）
router = APIRouter(prefix="/config", tags=["config"])  # 前缀/config，标签config（路由）
pattern_recognition = PatternRecognition()  # 模式识别实例（模式识别）

@router.post("/models", response_model=ModelConfigResponse)
def create_model_config_endpoint(config: ModelConfigCreate, db: Session = Depends(get_db)):
    """创建模型配置（创建模型配置）"""
    return create_model_config(
        db,
        name=config.name,
        api_base=config.api_base,
        api_key=config.api_key,
        model_id=config.model_id,
        is_default=config.is_default
    )

@router.get("/models", response_model=list[ModelConfigResponse])
def list_model_configs(db: Session = Depends(get_db)):
    """获取模型配置列表（获取配置列表）"""
    return get_model_configs(db)

@router.get("/models/default", response_model=ModelConfigResponse)
def get_default_config(db: Session = Depends(get_db)):
    """获取默认模型配置（获取默认配置）"""
    config = get_default_model_config(db)  # 获取默认（获取默认）
    if not config:
        raise HTTPException(status_code=404, detail="No default model config found")  # 抛出404（未找到）
    return config

@router.get("/models/{config_id}", response_model=ModelConfigResponse)
def get_model_config_detail(config_id: int, db: Session = Depends(get_db)):
    """获取模型配置详情（获取配置详情）"""
    config = get_model_config(db, config_id)  # 获取配置（获取）
    if not config:
        raise HTTPException(status_code=404, detail="Model config not found")  # 抛出404（未找到）
    return config

@router.put("/models/{config_id}", response_model=ModelConfigResponse)
def update_model_config_endpoint(config_id: int, config: ModelConfigUpdate, 
                                 db: Session = Depends(get_db)):
    """更新模型配置（更新模型配置）"""
    result = update_model_config(db, config_id, **config.dict(exclude_unset=True))  # 更新（更新）
    if not result:
        raise HTTPException(status_code=404, detail="Model config not found")  # 抛出404（未找到）
    return result

@router.delete("/models/{config_id}")
def delete_model_config_endpoint(config_id: int, db: Session = Depends(get_db)):
    """删除模型配置（删除模型配置）"""
    success = delete_model_config(db, config_id)  # 删除（删除）
    if not success:
        raise HTTPException(status_code=404, detail="Model config not found")  # 抛出404（未找到）
    return {"message": "Model config deleted successfully"}  # 返回成功（成功）

@router.post("/detect-patterns", response_model=PatternDetectionResponse)
def detect_patterns(request: PatternDetectionRequest):
    """检测模式（模式检测）"""
    patterns = pattern_recognition.detect_patterns(request.content)  # 检测模式（检测模式）
    variables = pattern_recognition.extract_variables(request.content)  # 提取变量（提取变量）
    suggested_tags = pattern_recognition.suggest_tags(request.content)  # 建议标签（建议标签）
    
    return PatternDetectionResponse(
        patterns=patterns,
        variables=variables,
        suggested_tags=suggested_tags
    )

@router.get("/dashboard-stats")
def get_dashboard_stats_endpoint(db: Session = Depends(get_db)):
    """获取仪表盘统计（获取仪表盘统计）"""
    from database.crud import get_dashboard_stats, get_recent_prompts, get_popular_prompts  # 动态导入（动态导入）
    
    stats = get_dashboard_stats(db)  # 获取统计（获取统计）
    recent = get_recent_prompts(db, limit=5)  # 最近更新（最近更新）
    popular = get_popular_prompts(db, limit=5)  # 热门提示词（热门）
    
    return {
        "stats": stats,
        "recent_prompts": [
            {"id": p.id, "title": p.title, "scenario": p.scenario, "updated_at": p.updated_at}
            for p in recent
        ],
        "popular_prompts": [
            {"id": p.id, "title": p.title, "scenario": p.scenario, "usage_count": p.usage_count}
            for p in popular
        ]
    }

@router.get("/scenarios")
def get_scenarios():
    """获取场景列表（获取场景）"""
    return {"scenarios": pattern_recognition.SCENARIOS}

@router.get("/patterns")
def get_patterns():
    """获取模式列表（获取模式）"""
    return {"patterns": list(pattern_recognition.PATTERNS.keys())}

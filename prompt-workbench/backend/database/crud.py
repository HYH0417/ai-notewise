import sys  # 系统模块
import os  # 文件系统模块

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session  # 数据库会话
from .models import Prompt, PromptVersion, ABTest, ModelConfig, Favorite  # 数据模型
from datetime import datetime  # 日期时间
from services.chroma_service import ChromaService  # 向量存储服务
from services.embedding_service import EmbeddingService  # 向量化服务
from utils.encryption import encrypt_api_key, decrypt_api_key  # 加密工具
import json  # JSON处理

# 初始化向量存储服务和向量化服务
chroma_service = ChromaService()  # 向量存储服务（向量数据库）
embedding_service = EmbeddingService()  # 向量化服务（文本转向量）


def create_prompt(db: Session, title: str, scenario: str, content: str, tags: list = None, 
                  model: str = None, change_note: str = None) -> Prompt:
    """创建新的Prompt（创建提示词）"""
    version = PromptVersion(
        version_number="v1",  # 版本号（初始版本）
        content=content,  # 内容（Prompt内容）
        variables=[],  # 变量列表（变量）
        change_note=change_note or "Initial version（初始版本）",  # 更新说明（更新说明）
        rating=None,  # 评分（评分）
        notes=None,  # 备注（备注）
        created_at=datetime.utcnow()  # 创建时间（创建时间）
    )
    
    prompt = Prompt(
        title=title,  # 标题（标题）
        scenario=scenario,  # 场景（场景）
        tags=tags or [],  # 标签（标签）
        model=model,  # 模型（模型名称）
        usage_count=0,  # 使用次数（使用次数）
        created_at=datetime.utcnow(),  # 创建时间（创建时间）
        updated_at=datetime.utcnow()  # 更新时间（更新时间）
    )
    prompt.versions.append(version)  # 添加初始版本（添加版本）
    
    db.add(prompt)  # 添加到数据库（添加到会话）
    db.flush()  # 先分配 prompt/version 主键，再设置 current_version_id
    prompt.current_version_id = version.id  # 设置当前版本ID（当前版本）
    db.commit()  # 提交事务（提交）
    db.refresh(prompt)  # 刷新对象（刷新）
    db.refresh(version)  # 刷新版本对象（刷新版本）
    
    # 向量化并同步到向量数据库
    embedding = embedding_service.encode(content)  # 编码为向量（向量化）
    chroma_service.add_prompt(prompt.id, content, embedding)  # 添加到向量存储（向量存储）
    
    return prompt


def get_prompt(db: Session, prompt_id: int) -> Prompt:
    """获取单个Prompt（获取提示词）"""
    from sqlalchemy.orm import joinedload  # 预加载关联数据（预加载）
    return db.query(Prompt).options(joinedload(Prompt.versions)).filter(Prompt.id == prompt_id).first()  # 查询并预加载版本（查询）


def get_prompts(db: Session, skip: int = 0, limit: int = 100, scenario: str = None, 
                tags: list = None, pattern: str = None, rating: int = None) -> dict:
    """获取Prompt列表（获取提示词列表）"""
    query = db.query(Prompt)  # 创建查询（创建查询）
    
    if scenario:
        query = query.filter(Prompt.scenario == scenario)  # 按场景筛选（场景筛选）
    
    if tags:
        query = query.filter(Prompt.tags.contains(tags))  # 按标签筛选（标签筛选）
    
    if pattern:
        query = query.filter(Prompt.tags.contains([pattern]))  # 按模式筛选（模式筛选）
    
    if rating:
        query = query.filter(
            Prompt.versions.any(PromptVersion.rating >= rating)  # 按评分筛选（评分筛选）
        )
    
    total = query.count()  # 计算总数（总数）
    items = query.order_by(Prompt.created_at.desc()).offset(skip).limit(limit).all()  # 排序分页返回（排序分页）
    
    return {"items": items, "total": total}


def update_prompt(db: Session, prompt_id: int, title: str = None, scenario: str = None, 
                  tags: list = None, model: str = None) -> Prompt:
    """更新Prompt（更新提示词）"""
    prompt = get_prompt(db, prompt_id)  # 获取Prompt（获取）
    if not prompt:
        return None  # 不存在返回None（不存在）
    
    if title:
        prompt.title = title  # 更新标题（更新标题）
    if scenario:
        prompt.scenario = scenario  # 更新场景（更新场景）
    if tags is not None:
        prompt.tags = tags  # 更新标签（更新标签）
    if model:
        prompt.model = model  # 更新模型（更新模型）
    
    prompt.updated_at = datetime.utcnow()  # 更新时间戳（更新时间）
    db.commit()  # 提交事务（提交）
    db.refresh(prompt)  # 刷新对象（刷新）
    
    return prompt


def delete_prompt(db: Session, prompt_id: int) -> bool:
    """删除Prompt（删除提示词）"""
    prompt = get_prompt(db, prompt_id)  # 获取Prompt（获取）
    if not prompt:
        return False  # 不存在返回False（不存在）
    
    chroma_service.delete_prompt(prompt_id)  # 从向量存储删除（向量删除）
    
    db.delete(prompt)  # 从数据库删除（数据库删除）
    db.commit()  # 提交事务（提交）
    
    return True


def increment_usage_count(db: Session, prompt_id: int):
    """增加使用次数（增加使用次数）"""
    prompt = get_prompt(db, prompt_id)  # 获取Prompt（获取）
    if prompt:
        prompt.usage_count += 1  # 使用次数+1（计数+1）
        db.commit()  # 提交事务（提交）


def create_prompt_version(db: Session, prompt_id: int, content: str, 
                          change_note: str = None) -> PromptVersion:
    """创建新版本（创建版本）"""
    prompt = get_prompt(db, prompt_id)  # 获取Prompt（获取）
    if not prompt:
        return None  # 不存在返回None（不存在）
    
    # 计算新版本号
    max_version = 0  # 最大版本号（最大版本）
    for v in prompt.versions:
        if v.version_number.startswith("v"):  # 检查版本号格式（版本格式）
            try:
                num = int(v.version_number[1:])  # 提取版本数字（提取数字）
                max_version = max(max_version, num)  # 更新最大版本（更新最大）
            except:
                pass
    
    new_version_number = f"v{max_version + 1}"  # 新的版本号（新版本号）
    
    version = PromptVersion(
        prompt_id=prompt_id,  # 关联Prompt（关联提示词）
        version_number=new_version_number,  # 版本号（版本号）
        content=content,  # 内容（内容）
        variables=[],  # 变量（变量）
        change_note=change_note,  # 更新说明（更新说明）
        rating=None,  # 评分（评分）
        notes=None,  # 备注（备注）
        created_at=datetime.utcnow()  # 创建时间（创建时间）
    )
    
    db.add(version)  # 添加版本（添加）
    db.flush()  # 先分配版本主键，再更新当前版本
    prompt.current_version_id = version.id  # 更新当前版本（更新当前）
    prompt.updated_at = datetime.utcnow()  # 更新时间（更新时间）
    db.commit()  # 提交事务（提交）
    db.refresh(version)  # 刷新版本（刷新）
    
    # 更新向量存储
    chroma_service.delete_prompt(prompt_id)  # 删除旧向量（删除旧向量）
    embedding = embedding_service.encode(content)  # 编码新向量（编码）
    chroma_service.add_prompt(prompt_id, content, embedding)  # 添加新向量（添加新向量）
    
    return version


def get_prompt_versions(db: Session, prompt_id: int) -> list:
    """获取Prompt的所有版本（获取版本列表）"""
    return db.query(PromptVersion)\
        .filter(PromptVersion.prompt_id == prompt_id)\
        .order_by(PromptVersion.created_at.asc())\
        .all()


def get_prompt_version(db: Session, version_id: int) -> PromptVersion:
    """获取单个版本（获取版本）"""
    return db.query(PromptVersion).filter(PromptVersion.id == version_id).first()


def update_prompt_version(db: Session, version_id: int, content: str = None, 
                          change_note: str = None, rating: int = None, notes: str = None) -> PromptVersion:
    """更新版本（更新版本）"""
    version = get_prompt_version(db, version_id)  # 获取版本（获取）
    if not version:
        return None  # 不存在返回None（不存在）
    
    if content is not None:
        version.content = content  # 更新内容（更新内容）
        
        # 更新向量存储
        chroma_service.delete_prompt(version.prompt_id)  # 删除旧向量（删除旧向量）
        embedding = embedding_service.encode(content)  # 编码新向量（编码）
        chroma_service.add_prompt(version.prompt_id, content, embedding)  # 添加新向量（添加新向量）
    
    if change_note is not None:
        version.change_note = change_note  # 更新说明（更新说明）
    if rating is not None:
        version.rating = rating  # 更新评分（更新评分）
    if notes is not None:
        version.notes = notes  # 更新备注（更新备注）
    
    db.commit()  # 提交事务（提交）
    db.refresh(version)  # 刷新版本（刷新）
    
    # 如果是当前版本，更新Prompt的更新时间
    prompt = get_prompt(db, version.prompt_id)  # 获取Prompt（获取提示词）
    if prompt and prompt.current_version_id == version.id:  # 检查是否当前版本（检查当前）
        prompt.updated_at = datetime.utcnow()  # 更新时间（更新时间）
        db.commit()  # 提交事务（提交）
    
    return version


def create_ab_test(db: Session, test_input: str, version_a_id: int, 
                   version_b_id: int, output_a: str = None, output_b: str = None) -> ABTest:
    """创建A/B测试（创建A/B测试）"""
    ab_test = ABTest(
        test_input=test_input,  # 测试输入（测试输入）
        version_a_id=version_a_id,  # 版本A（版本A）
        version_b_id=version_b_id,  # 版本B（版本B）
        output_a=output_a,  # 输出A（输出A）
        output_b=output_b,  # 输出B（输出B）
        rating_a=None,  # 评分A（评分A）
        rating_b=None,  # 评分B（评分B）
        evaluation=None,  # 评估（评估）
        created_at=datetime.utcnow()  # 创建时间（创建时间）
    )
    db.add(ab_test)  # 添加到数据库（添加）
    db.commit()  # 提交事务（提交）
    db.refresh(ab_test)  # 刷新对象（刷新）
    return ab_test


def update_ab_test(db: Session, test_id: int, output_a: str = None, output_b: str = None,
                   rating_a: int = None, rating_b: int = None, evaluation: str = None) -> ABTest:
    """更新A/B测试（更新A/B测试）"""
    ab_test = db.query(ABTest).filter(ABTest.id == test_id).first()  # 获取测试（获取）
    if not ab_test:
        return None  # 不存在返回None（不存在）
    
    if output_a is not None:
        ab_test.output_a = output_a  # 更新输出A（更新输出A）
    if output_b is not None:
        ab_test.output_b = output_b  # 更新输出B（更新输出B）
    if rating_a is not None:
        ab_test.rating_a = rating_a  # 更新评分A（更新评分A）
    if rating_b is not None:
        ab_test.rating_b = rating_b  # 更新评分B（更新评分B）
    if evaluation is not None:
        ab_test.evaluation = evaluation  # 更新评估（更新评估）
    
    db.commit()  # 提交事务（提交）
    db.refresh(ab_test)  # 刷新对象（刷新）
    return ab_test


def get_ab_test(db: Session, test_id: int) -> ABTest:
    """获取单个A/B测试（获取A/B测试）"""
    return db.query(ABTest).filter(ABTest.id == test_id).first()


def get_ab_tests(db: Session, prompt_id: int = None, skip: int = 0, limit: int = 100) -> list:
    """获取A/B测试列表（获取A/B测试列表）"""
    query = db.query(ABTest)  # 创建查询（创建查询）
    if prompt_id:
        query = query.filter(
            (ABTest.version_a_id.in_(
                db.query(PromptVersion.id).filter(PromptVersion.prompt_id == prompt_id)
            )) | (ABTest.version_b_id.in_(
                db.query(PromptVersion.id).filter(PromptVersion.prompt_id == prompt_id)
            ))
        )  # 按Prompt筛选（按提示词筛选）
    return query.order_by(ABTest.created_at.desc()).offset(skip).limit(limit).all()  # 排序分页（排序分页）


def create_model_config(db: Session, name: str, api_base: str, api_key: str, 
                        model_id: str, is_default: bool = False) -> ModelConfig:
    """创建模型配置（创建模型配置）"""
    if is_default:
        db.query(ModelConfig).filter(ModelConfig.is_default == True).update({"is_default": False})  # 取消其他默认（取消默认）
    
    config = ModelConfig(
        name=name,  # 配置名称（配置名称）
        api_base=api_base,  # API基础URL（API基础URL）
        api_key=encrypt_api_key(api_key),  # 加密的API密钥（加密密钥）
        model_id=model_id,  # 模型ID（模型ID）
        is_default=is_default,  # 是否默认（是否默认）
        created_at=datetime.utcnow()  # 创建时间（创建时间）
    )
    db.add(config)  # 添加到数据库（添加）
    db.commit()  # 提交事务（提交）
    db.refresh(config)  # 刷新对象（刷新）
    return config


def get_model_config(db: Session, config_id: int) -> ModelConfig:
    """获取模型配置（获取模型配置）"""
    return db.query(ModelConfig).filter(ModelConfig.id == config_id).first()


def get_model_configs(db: Session) -> list:
    """获取所有模型配置（获取模型配置列表）"""
    return db.query(ModelConfig).all()


def get_default_model_config(db: Session) -> ModelConfig:
    """获取默认模型配置（获取默认配置）"""
    return db.query(ModelConfig).filter(ModelConfig.is_default == True).first()


def update_model_config(db: Session, config_id: int, name: str = None, api_base: str = None,
                        api_key: str = None, model_id: str = None, is_default: bool = None) -> ModelConfig:
    """更新模型配置（更新模型配置）"""
    config = get_model_config(db, config_id)  # 获取配置（获取）
    if not config:
        return None  # 不存在返回None（不存在）
    
    if is_default:
        db.query(ModelConfig).filter(ModelConfig.is_default == True).update({"is_default": False})  # 取消其他默认（取消默认）
        config.is_default = True  # 设置为默认（设为默认）
    
    if name is not None:
        config.name = name  # 更新名称（更新名称）
    if api_base is not None:
        config.api_base = api_base  # 更新API基础URL（更新API基础）
    if api_key is not None:
        config.api_key = encrypt_api_key(api_key)  # 更新加密密钥（更新密钥）
    if model_id is not None:
        config.model_id = model_id  # 更新模型ID（更新模型）
    
    db.commit()  # 提交事务（提交）
    db.refresh(config)  # 刷新对象（刷新）
    return config


def delete_model_config(db: Session, config_id: int) -> bool:
    """删除模型配置（删除模型配置）"""
    config = get_model_config(db, config_id)  # 获取配置（获取）
    if not config:
        return False  # 不存在返回False（不存在）
    
    db.delete(config)  # 删除配置（删除）
    db.commit()  # 提交事务（提交）
    return True


def get_dashboard_stats(db: Session):
    """获取仪表盘统计数据（获取仪表盘统计）"""
    total = db.query(Prompt).count()  # 总Prompt数（总数）
    
    from datetime import timedelta
    one_week_ago = datetime.utcnow() - timedelta(days=7)  # 一周前（一周前）
    weekly_new = db.query(Prompt).filter(Prompt.created_at >= one_week_ago).count()  # 本周新增（本周新增）
    
    # 平均评分（平均评分）
    avg_rating = db.query(PromptVersion.rating).filter(PromptVersion.rating.isnot(None)).all()
    if avg_rating:
        avg_rating = round(sum(r[0] for r in avg_rating) / len(avg_rating), 1)  # 计算平均值（计算平均）
    else:
        avg_rating = 0.0  # 默认值（默认）
    
    # 热门场景（热门场景）
    from sqlalchemy import func
    scenario_counts = db.query(
        Prompt.scenario, func.count(Prompt.id)
    ).group_by(Prompt.scenario).order_by(func.count(Prompt.id).desc()).limit(5).all()  # 按场景统计（场景统计）
    popular_scenarios = [{"scenario": s, "count": c} for s, c in scenario_counts]  # 转换为列表（转换）
    
    return {
        "total_prompts": total,  # 总提示词数（总数）
        "weekly_new": weekly_new,  # 本周新增（本周新增）
        "avg_rating": avg_rating,  # 平均评分（平均分）
        "popular_scenarios": popular_scenarios  # 热门场景（热门场景）
    }


def get_recent_prompts(db: Session, limit: int = 5):
    """获取最近更新的Prompt（获取最近更新）"""
    return db.query(Prompt).order_by(Prompt.updated_at.desc()).limit(limit).all()


def get_popular_prompts(db: Session, limit: int = 5):
    """获取最热门的Prompt（获取热门提示词）"""
    return db.query(Prompt).order_by(Prompt.usage_count.desc()).limit(limit).all()


def add_favorite(db: Session, prompt_id: int) -> Favorite:
    """添加收藏（添加收藏）"""
    existing = db.query(Favorite).filter(Favorite.prompt_id == prompt_id).first()  # 检查是否已收藏（检查）
    if existing:
        return existing  # 已存在则返回（已存在）
    
    favorite = Favorite(
        prompt_id=prompt_id,  # 关联提示词（关联提示词）
        created_at=datetime.utcnow()  # 创建时间（创建时间）
    )
    db.add(favorite)  # 添加到数据库（添加）
    db.commit()  # 提交事务（提交）
    db.refresh(favorite)  # 刷新对象（刷新）
    return favorite


def remove_favorite(db: Session, prompt_id: int) -> bool:
    """取消收藏（取消收藏）"""
    favorite = db.query(Favorite).filter(Favorite.prompt_id == prompt_id).first()  # 获取收藏（获取）
    if not favorite:
        return False  # 不存在返回False（不存在）
    
    db.delete(favorite)  # 删除收藏（删除）
    db.commit()  # 提交事务（提交）
    return True


def is_favorite(db: Session, prompt_id: int) -> bool:
    """检查是否已收藏（检查收藏状态）"""
    return db.query(Favorite).filter(Favorite.prompt_id == prompt_id).first() is not None  # 查询（查询）


def get_favorites(db: Session, skip: int = 0, limit: int = 100) -> dict:
    """获取收藏列表（获取收藏列表）"""
    query = db.query(Prompt).join(Favorite, Prompt.id == Favorite.prompt_id)  # 关联查询（关联查询）
    
    total = query.count()  # 计算总数（总数）
    items = query.order_by(Favorite.created_at.desc()).offset(skip).limit(limit).all()  # 排序分页（排序分页）
    
    return {"items": items, "total": total}


def get_favorite_count(db: Session) -> int:
    """获取收藏数量（获取收藏数量）"""
    return db.query(Favorite).count()  # 统计数量（统计）


def get_favorite_status(db: Session, prompt_ids: list[int]) -> dict:
    """批量获取收藏状态（批量获取收藏状态）"""
    favorites = db.query(Favorite.prompt_id).filter(Favorite.prompt_id.in_(prompt_ids)).all()  # 查询收藏ID列表（查询）
    favorite_ids = set(f[0] for f in favorites)  # 转换为集合（转换）
    
    result = {}
    for pid in prompt_ids:
        result[pid] = pid in favorite_ids  # 设置状态（设置状态）
    
    return result

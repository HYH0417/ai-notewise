from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean, ForeignKey  # 导入SQLAlchemy列类型
from sqlalchemy.ext.declarative import declarative_base  # 声明式基类
from sqlalchemy.orm import relationship  # 关系映射
from datetime import datetime  # 日期时间

# 创建声明式基类，所有模型继承此类
Base = declarative_base()  # 声明式基类（ORM基类）


class Prompt(Base):
    """Prompt主表（提示词主表）"""
    __tablename__ = "prompts"  # 表名：prompts（提示词）
    
    id = Column(Integer, primary_key=True, index=True)  # 主键ID（主键）
    title = Column(String(255), nullable=False)  # 标题（标题）
    scenario = Column(String(50), nullable=False)  # 场景（场景）
    tags = Column(JSON, default=[])  # 标签（标签）
    model = Column(String(100), nullable=True)  # 关联模型（模型名称）
    usage_count = Column(Integer, default=0)  # 使用次数（使用次数）
    current_version_id = Column(Integer)  # 当前版本ID（当前版本ID）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间（创建时间）
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间（更新时间）
    
    # 关联关系：一个Prompt对应多个版本
    versions = relationship("PromptVersion", back_populates="prompt", cascade="all, delete-orphan")  # 版本列表（版本关系）


class PromptVersion(Base):
    """Prompt版本表（提示词版本表）"""
    __tablename__ = "prompt_versions"  # 表名：prompt_versions（提示词版本）
    
    id = Column(Integer, primary_key=True, index=True)  # 主键ID（主键）
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=False)  # 关联Prompt的外键（关联提示词ID）
    version_number = Column(String(20), nullable=False)  # 版本号（版本号）
    content = Column(Text, nullable=False)  # 内容（内容）
    variables = Column(JSON, default=[])  # 变量列表（变量）
    change_note = Column(String(500), nullable=True)  # 更新说明（更新说明）
    rating = Column(Integer, nullable=True)  # 评分（评分）
    notes = Column(Text, nullable=True)  # 备注（备注）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间（创建时间）
    
    # 关联关系：一个版本属于一个Prompt
    prompt = relationship("Prompt", back_populates="versions")  # 关联提示词（提示词关系）


class ABTest(Base):
    """A/B测试表（A/B测试表）"""
    __tablename__ = "ab_tests"  # 表名：ab_tests（A/B测试）
    
    id = Column(Integer, primary_key=True, index=True)  # 主键ID（主键）
    test_input = Column(Text, nullable=False)  # 测试输入（测试输入）
    version_a_id = Column(Integer, ForeignKey("prompt_versions.id"), nullable=False)  # 版本A的ID（版本A）
    version_b_id = Column(Integer, ForeignKey("prompt_versions.id"), nullable=False)  # 版本B的ID（版本B）
    output_a = Column(Text, nullable=True)  # A版本输出（输出A）
    output_b = Column(Text, nullable=True)  # B版本输出（输出B）
    rating_a = Column(Integer, nullable=True)  # A版本评分（评分A）
    rating_b = Column(Integer, nullable=True)  # B版本评分（评分B）
    evaluation = Column(Text, nullable=True)  # 评估结果（评估）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间（创建时间）


class ModelConfig(Base):
    """模型配置表（模型配置表）"""
    __tablename__ = "model_configs"  # 表名：model_configs（模型配置）
    
    id = Column(Integer, primary_key=True, index=True)  # 主键ID（主键）
    name = Column(String(100), nullable=False)  # 配置名称（配置名称）
    api_base = Column(String(500), nullable=False)  # API基础URL（API基础URL）
    api_key = Column(Text, nullable=False)  # API密钥（加密存储）（API密钥）
    model_id = Column(String(200), nullable=False)  # 模型ID（模型ID）
    is_default = Column(Boolean, default=False)  # 是否默认配置（是否默认）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间（创建时间）


class Favorite(Base):
    """收藏表（收藏表）"""
    __tablename__ = "favorites"  # 表名：favorites（收藏）
    
    id = Column(Integer, primary_key=True, index=True)  # 主键ID（主键）
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=False)  # 关联Prompt的外键（关联提示词ID）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间（创建时间）

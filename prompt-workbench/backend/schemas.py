from pydantic import BaseModel  # Pydantic模型基类（数据验证）
from datetime import datetime  # 日期时间（日期时间）
from typing import Optional, List  # 类型提示（类型提示）


class PromptCreate(BaseModel):
    """创建Prompt请求（创建提示词请求）"""
    title: str  # 标题（标题）
    scenario: str  # 场景（场景）
    content: str  # 内容（内容）
    tags: List[str] = []  # 标签列表（标签）
    model: Optional[str] = None  # 模型名称（模型）
    change_note: Optional[str] = None  # 更新说明（更新说明）


class PromptUpdate(BaseModel):
    """更新Prompt请求（更新提示词请求）"""
    title: Optional[str] = None  # 标题（标题）
    scenario: Optional[str] = None  # 场景（场景）
    tags: Optional[List[str]] = None  # 标签列表（标签）
    model: Optional[str] = None  # 模型名称（模型）


class PromptResponse(BaseModel):
    """Prompt响应（提示词响应）"""
    id: int  # ID（ID）
    title: str  # 标题（标题）
    scenario: str  # 场景（场景）
    tags: List[str]  # 标签列表（标签）
    model: Optional[str]  # 模型名称（模型）
    usage_count: int  # 使用次数（使用次数）
    current_version_id: Optional[int]  # 当前版本ID（当前版本ID）
    created_at: datetime  # 创建时间（创建时间）
    updated_at: datetime  # 更新时间（更新时间）
    versions: List['PromptVersionResponse'] = []  # 版本列表（版本列表）
    
    class Config:
        from_attributes = True  # 从ORM对象加载（从ORM加载）


class PromptDetailResponse(BaseModel):
    """Prompt详情响应（提示词详情响应）"""
    id: int  # ID（ID）
    title: str  # 标题（标题）
    scenario: str  # 场景（场景）
    tags: List[str]  # 标签列表（标签）
    model: Optional[str]  # 模型名称（模型）
    usage_count: int  # 使用次数（使用次数）
    current_version_id: Optional[int]  # 当前版本ID（当前版本ID）
    created_at: datetime  # 创建时间（创建时间）
    updated_at: datetime  # 更新时间（更新时间）
    versions: List['PromptVersionResponse'] = []  # 版本列表（版本列表）
    
    class Config:
        from_attributes = True  # 从ORM对象加载（从ORM加载）


class PromptVersionCreate(BaseModel):
    """创建版本请求（创建版本请求）"""
    content: str  # 内容（内容）
    change_note: Optional[str] = None  # 更新说明（更新说明）


class PromptVersionUpdate(BaseModel):
    """更新版本请求（更新版本请求）"""
    content: Optional[str] = None  # 内容（内容）
    change_note: Optional[str] = None  # 更新说明（更新说明）
    rating: Optional[int] = None  # 评分（评分）
    notes: Optional[str] = None  # 备注（备注）


class PromptVersionResponse(BaseModel):
    """版本响应（版本响应）"""
    id: int  # ID（ID）
    prompt_id: int  # PromptID（提示词ID）
    version_number: str  # 版本号（版本号）
    content: str  # 内容（内容）
    variables: List[str] = []  # 变量列表（变量）
    change_note: Optional[str] = None  # 更新说明（更新说明）
    rating: Optional[int] = None  # 评分（评分）
    notes: Optional[str] = None  # 备注（备注）
    created_at: datetime  # 创建时间（创建时间）
    
    class Config:
        from_attributes = True  # 从ORM对象加载（从ORM加载）


class ABTestCreate(BaseModel):
    """创建A/B测试请求（创建A/B测试请求）"""
    test_input: str  # 测试输入（测试输入）
    version_a_id: int  # 版本A（版本A）
    version_b_id: int  # 版本B（版本B）
    model_config_id: Optional[int] = None  # 模型配置ID（模型配置ID）


class ABTestUpdate(BaseModel):
    """更新A/B测试请求（更新A/B测试请求）"""
    output_a: Optional[str] = None  # 输出A（输出A）
    output_b: Optional[str] = None  # 输出B（输出B）
    rating_a: Optional[int] = None  # 评分A（评分A）
    rating_b: Optional[int] = None  # 评分B（评分B）
    evaluation: Optional[str] = None  # 评估（评估）


class ABTestResponse(BaseModel):
    """A/B测试响应（A/B测试响应）"""
    id: int  # ID（ID）
    test_input: str  # 测试输入（测试输入）
    version_a_id: int  # 版本A（版本A）
    version_b_id: int  # 版本B（版本B）
    output_a: Optional[str] = None  # 输出A（输出A）
    output_b: Optional[str] = None  # 输出B（输出B）
    rating_a: Optional[int] = None  # 评分A（评分A）
    rating_b: Optional[int] = None  # 评分B（评分B）
    evaluation: Optional[str] = None  # 评估（评估）
    created_at: datetime  # 创建时间（创建时间）
    
    class Config:
        from_attributes = True  # 从ORM对象加载（从ORM加载）


class ModelConfigCreate(BaseModel):
    """创建模型配置请求（创建模型配置请求）"""
    name: str  # 配置名称（配置名称）
    api_base: str  # API基础URL（API基础URL）
    api_key: str  # API密钥（API密钥）
    model_id: str  # 模型ID（模型ID）
    is_default: bool = False  # 是否默认（是否默认）


class ModelConfigUpdate(BaseModel):
    """更新模型配置请求（更新模型配置请求）"""
    name: Optional[str] = None  # 配置名称（配置名称）
    api_base: Optional[str] = None  # API基础URL（API基础URL）
    api_key: Optional[str] = None  # API密钥（API密钥）
    model_id: Optional[str] = None  # 模型ID（模型ID）
    is_default: Optional[bool] = None  # 是否默认（是否默认）


class ModelConfigResponse(BaseModel):
    """模型配置响应（模型配置响应）"""
    id: int  # ID（ID）
    name: str  # 配置名称（配置名称）
    api_base: str  # API基础URL（API基础URL）
    model_id: str  # 模型ID（模型ID）
    is_default: bool  # 是否默认（是否默认）
    created_at: datetime  # 创建时间（创建时间）
    
    class Config:
        from_attributes = True  # 从ORM对象加载（从ORM加载）


class DashboardStats(BaseModel):
    """仪表盘统计（仪表盘统计）"""
    total_prompts: int  # 总提示词数（总数）
    weekly_new: int  # 本周新增（本周新增）
    avg_rating: float  # 平均评分（平均分）
    popular_scenarios: List[dict]  # 热门场景（热门场景）


class SearchRequest(BaseModel):
    """搜索请求（搜索请求）"""
    query: str  # 查询词（查询词）
    top_k: int = 10  # 返回数量（返回数量）
    scenario: str = None  # 场景筛选（场景）
    tags: list = None  # 标签筛选（标签）


class SearchResult(BaseModel):
    """搜索结果（搜索结果）"""
    prompt_id: int  # PromptID（提示词ID）
    title: str  # 标题（标题）
    content: str  # 内容（内容）
    score: Optional[float] = None  # 分数（分数）
    scenario: str = None  # 场景（场景）
    similarity: float = None  # 相似度（相似度）


class ABTestRunRequest(BaseModel):
    """运行A/B测试请求（运行A/B测试请求）"""
    test_input: str  # 测试输入（测试输入）
    prompt_version_a_id: int  # 版本A（版本A）
    prompt_version_b_id: int  # 版本B（版本B）
    model_config_id: Optional[int] = None  # 模型配置ID（模型配置ID）


class ABTestRunResponse(BaseModel):
    """运行A/B测试响应（运行A/B测试响应）"""
    test_id: int  # 测试ID（测试ID）
    output_a: str  # 输出A（输出A）
    output_b: str  # 输出B（输出B）


class PatternDetectionRequest(BaseModel):
    """模式检测请求（模式检测请求）"""
    content: str  # 内容（内容）


class PatternDetectionResponse(BaseModel):
    """模式检测响应（模式检测响应）"""
    patterns: List[str]  # 模式列表（模式）
    variables: List[str]  # 变量列表（变量）
    suggested_tags: List[str]  # 建议标签（建议标签）

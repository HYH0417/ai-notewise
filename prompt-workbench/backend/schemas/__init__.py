from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class PromptCreate(BaseModel):
    title: str
    scenario: str
    content: str
    tags: Optional[List[str]] = []
    model: Optional[str] = None
    change_note: Optional[str] = None

class PromptUpdate(BaseModel):
    title: Optional[str] = None
    scenario: Optional[str] = None
    tags: Optional[List[str]] = None
    model: Optional[str] = None

class PromptResponse(BaseModel):
    id: int
    title: str
    scenario: str
    tags: List[str]
    model: Optional[str]
    usage_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class PromptDetailResponse(PromptResponse):
    current_version: Optional["PromptVersionResponse"] = None
    versions: List["PromptVersionResponse"] = []

class PromptVersionCreate(BaseModel):
    content: str
    change_note: Optional[str] = None

class PromptVersionUpdate(BaseModel):
    content: Optional[str] = None
    change_note: Optional[str] = None
    rating: Optional[int] = None
    notes: Optional[str] = None

class PromptVersionResponse(BaseModel):
    id: int
    version_number: str
    content: str
    variables: List[str]
    change_note: Optional[str]
    rating: Optional[int]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        orm_mode = True

class ABTestCreate(BaseModel):
    test_input: str
    version_a_id: int
    version_b_id: int
    model_config_id: Optional[int] = None

class ABTestUpdate(BaseModel):
    rating_a: Optional[int] = None
    rating_b: Optional[int] = None
    evaluation: Optional[str] = None

class ABTestResponse(BaseModel):
    id: int
    test_input: str
    version_a_id: int
    version_b_id: int
    output_a: Optional[str]
    output_b: Optional[str]
    rating_a: Optional[int]
    rating_b: Optional[int]
    evaluation: Optional[str]
    created_at: datetime
    
    class Config:
        orm_mode = True

class ModelConfigCreate(BaseModel):
    name: str
    api_base: str
    api_key: str
    model_id: str
    is_default: Optional[bool] = False

class ModelConfigUpdate(BaseModel):
    name: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    model_id: Optional[str] = None
    is_default: Optional[bool] = None

class ModelConfigResponse(BaseModel):
    id: int
    name: str
    api_base: str
    model_id: str
    is_default: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

class SearchRequest(BaseModel):
    query: str
    scenario: Optional[str] = None
    tags: Optional[List[str]] = None
    top_k: Optional[int] = 10

class SearchResult(BaseModel):
    prompt_id: int
    title: str
    scenario: str
    similarity: float
    content: str

class PatternDetectionRequest(BaseModel):
    content: str

class PatternDetectionResponse(BaseModel):
    patterns: List[str]
    variables: List[str]
    suggested_tags: List[str]

class DashboardStats(BaseModel):
    total_prompts: int
    weekly_new: int
    avg_rating: float
    popular_scenarios: List[Dict[str, str]]

class CopyRequest(BaseModel):
    prompt_id: int
    variables: Dict[str, str] = {}

PromptDetailResponse.update_forward_refs()

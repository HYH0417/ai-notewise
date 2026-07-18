# Agent Skills Library — 提示词工程工作台

收集、检索、管理和 A/B 测试高质量 AI Agent Skills 的一体化工作台。

## 功能

- **Skills 管理** — 浏览、新增、编辑和删除 Agent Skills，每条 Skill 包含适用场景、执行流程、输入输出、质量标准与来源链接
- **语义检索** — 基于向量嵌入的全文语义搜索，快速找到最匹配的 Skill
- **A/B 测试** — 对同一个 Skill 的不同版本进行对比测试，量化评估效果差异
- **收藏系统** — 收藏常用 Skill，方便快速访问

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python, FastAPI, SQLite |
| 前端 | 原生 HTML / CSS / JavaScript |
| 向量检索 | ChromaDB, sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) |
| 数据存储 | SQLite (prompts, versions, favorites, ab_tests, model_configs) |

## 快速开始

```bash
# 安装后端依赖
cd prompt-workbench/backend
pip install -r requirements.txt

# 启动服务
python main.py

# 打开浏览器访问
# http://localhost:8000
```

首次启动会自动初始化数据库并预置 40 个来自公开来源的 Agent Skills。

## 项目结构

```
├── prompt-workbench/        # 主应用
│   ├── backend/             # FastAPI 后端
│   │   ├── api/             # API 路由
│   │   ├── database/        # 数据库模型和 CRUD
│   │   ├── schemas/         # 数据模型
│   │   ├── services/        # 业务逻辑（向量检索、嵌入、AB测试）
│   │   └── utils/           # 工具函数
│   ├── frontend/            # 前端页面
│   │   ├── css/
│   │   ├── js/
│   │   └── *.html
│   └── scripts/             # 数据初始化脚本
├── skill_folders/           # Agent Skills 源文件（SKILL.md + source.json）
├── vector_db/               # 向量数据库文件（已 gitignore）
└── prompt_workbench.db      # SQLite 数据库（已 gitignore）
```

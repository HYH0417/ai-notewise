import hashlib
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB_PATHS = [ROOT / "prompt_workbench.db", ROOT / "prompt-workbench" / "backend" / "prompt_workbench.db"]
SKILL_ROOT = ROOT / "skill_folders"
VECTOR_PATH = ROOT / "vector_db" / "vectors.json"
DESKTOP_SKILL_ROOT = Path.home() / "Desktop" / "DHPskills"
DIM = 384


def gh(path: str) -> str:
    if path.startswith("http"):
        return path
    return f"https://github.com/anthropics/claude-cookbooks/blob/main/{path}"


BASE_SKILLS = [
    ("代码审查 Agent", "代码", ["代码", "审查", "质量"], "按安全、回归、测试、可维护性检查代码变更。", gh(".claude/agents/code-reviewer.md")),
    ("教程审计 Skill", "办公", ["审计", "评分", "文档"], "用评分表审查教程、Notebook 或长文档。", gh(".claude/skills/cookbook-audit/SKILL.md")),
    ("CSV 数据分析 Agent", "办公", ["数据", "表格", "报告"], "把 CSV 转成带图表、洞察和后续问题的分析报告。", gh("managed_agents/data_analyst_agent.ipynb")),
    ("Slack 数据分析机器人", "办公", ["Slack", "数据", "协作"], "在团队沟通场景中接收数据文件并在线程里产出分析结论。", gh("managed_agents/slack_data_bot.ipynb")),
    ("失败测试修复 Agent", "代码", ["测试", "调试", "自动修复"], "读取失败测试，定位代码问题，修改并复跑。", gh("managed_agents/CMA_iterate_fix_failing_tests.ipynb")),
    ("生产级 Agent 部署", "运营", ["部署", "MCP", "生产"], "配置凭证、Webhook、人审节点和资源生命周期。", gh("managed_agents/CMA_operate_in_production.ipynb")),
    ("SRE 事件响应 Agent", "运营", ["SRE", "告警", "故障"], "处理线上告警，读取日志和 Runbook，定位根因并生成复盘材料。", gh("managed_agents/sre_incident_responder.ipynb")),
    ("提示词版本回滚", "运营", ["版本", "回滚", "评测"], "管理提示词版本、跑回归测试、发现退化并回滚。", gh("managed_agents/CMA_prompt_versioning_and_rollback.ipynb")),
    ("威胁情报分析 Agent", "安全", ["安全", "IOC", "威胁情报"], "调查 IOC，交叉验证威胁情报并输出结构化报告。", gh("tool_use/threat_intel_enrichment_agent.ipynb")),
    ("知识图谱构建 Skill", "知识库", ["知识图谱", "实体抽取", "RAG"], "从非结构化文本里抽实体、关系、去重并支持检索。", gh("capabilities/knowledge_graph/guide.ipynb")),
    ("图片局部裁剪分析", "办公", ["图片", "视觉", "文档"], "分析图表、截图、文档时先裁剪关键区域再回答。", gh("multimodal/crop_tool.ipynb")),
    ("程序化工具调用", "工具", ["工具调用", "API", "效率"], "让 Agent 编写代码批量调用工具，降低多工具任务成本。", gh("tool_use/programmatic_tool_calling_ptc.ipynb")),
    ("工具语义搜索", "工具", ["工具库", "检索", "Embedding"], "工具数量很多时，用语义检索选出最相关的工具。", gh("tool_use/tool_search_with_embeddings.ipynb")),
    ("长任务上下文压缩", "工具", ["上下文", "长期任务", "压缩"], "自动压缩长对话历史，保留关键状态。", gh("tool_use/automatic-context-compaction.ipynb")),
    ("上下文工程工具箱", "工具", ["记忆", "上下文", "工作流"], "比较记忆、压缩、工具清理等长期 Agent 上下文策略。", gh("tool_use/context_engineering/context_engineering_tools.ipynb")),
    ("前端审美生成 Skill", "代码", ["前端", "设计", "UI"], "指导 Agent 生成更像真实产品的前端界面。", gh("coding/prompting_for_frontend_aesthetics.ipynb")),
    ("分类系统构建", "办公", ["分类", "RAG", "工单"], "用检索上下文、评分表和结构化输出搭建文本分类或工单路由。", gh("capabilities/classification/guide.ipynb")),
    ("上下文增强检索", "知识库", ["RAG", "检索", "上下文"], "在文本块嵌入前补充上下文，提高 RAG 准确率。", gh("capabilities/contextual-embeddings/guide.ipynb")),
    ("RAG 系统优化", "知识库", ["RAG", "重排", "知识库"], "用摘要索引、重排和引用检查优化问答知识库。", gh("capabilities/retrieval_augmented_generation/guide.ipynb")),
    ("法律文档总结", "办公", ["总结", "法律", "文档"], "对长法律文档做结构化摘要，保留限制、风险和证据依据。", gh("capabilities/summarization/guide.ipynb")),
    ("自然语言转 SQL", "办公", ["SQL", "数据", "分析"], "结合数据库 schema，把业务问题转成 SQL 并校验。", gh("capabilities/text_to_sql/guide.ipynb")),
    ("研究简报 Agent", "产品", ["调研", "搜索", "简报"], "自动规划搜索、收集来源、写出带引用的研究简报。", gh("claude_agent_sdk/00_The_one_liner_research_agent.ipynb")),
    ("多 Agent 总协调", "运营", ["多 Agent", "协调", "规划"], "把复杂任务拆给多个子 Agent，汇总产物并控制节奏。", gh("claude_agent_sdk/01_The_chief_of_staff_agent.ipynb")),
    ("可观测 Agent", "运营", ["GitHub", "CI", "监控"], "通过 MCP 接入外部系统，监控 GitHub、CI 和工程流程。", gh("claude_agent_sdk/02_The_observability_agent.ipynb")),
    ("站点可靠性 Agent", "运营", ["诊断", "修复", "复盘"], "用读写工具完成故障诊断、修复建议和事故复盘。", gh("claude_agent_sdk/03_The_site_reliability_agent.ipynb")),
    ("Agent SDK 迁移", "代码", ["迁移", "SDK", "工具"], "把 Agent 应用里的工具、护栏、会话和交接迁移到新运行时。", gh("claude_agent_sdk/04_migrating_from_openai_agents_sdk.ipynb")),
    ("会话浏览器构建", "工具", ["会话", "历史", "管理"], "读取、重命名、打标签和分发 Agent 会话。", gh("claude_agent_sdk/05_Building_a_session_browser.ipynb")),
    ("漏洞发现 Agent", "安全", ["漏洞", "C 语言", "安全"], "对 C 代码做威胁建模，发现内存安全问题并输出分级报告。", gh("claude_agent_sdk/06_The_vulnerability_detection_agent.ipynb")),
    ("研究 Agent 托管", "运营", ["部署", "Docker", "Kubernetes"], "把研究 Agent 部署到 Docker、Modal 或 Kubernetes。", gh("claude_agent_sdk/07_Hosting_the_agent.ipynb")),
    ("复杂推理工作流", "工具", ["推理", "预算", "多步骤"], "为复杂任务分配推理预算，同时保持输出可验证。", gh("extended_thinking/extended_thinking.ipynb")),
    ("工具增强复杂推理", "工具", ["推理", "工具", "证据"], "把复杂推理和工具调用结合，用证据支撑结论。", gh("extended_thinking/extended_thinking_with_tool_use.ipynb")),
    ("批处理任务 Skill", "运营", ["批处理", "异步", "成本"], "异步处理大量模型请求，降低成本并追踪状态。", gh("misc/batch_processing.ipynb")),
    ("评测体系构建", "运营", ["评测", "指标", "质量"], "建立评测集、指标和回归监控，用数据改进 Prompt 或 Agent。", gh("misc/building_evals.ipynb")),
    ("内容审核过滤器", "安全", ["审核", "规则", "分类"], "定义规则、风险类别和输出结构，构建可配置审核过滤器。", gh("misc/building_moderation_filter.ipynb")),
    ("合成测试数据生成", "运营", ["测试数据", "评测", "样例"], "为 Prompt 或产品流程生成高覆盖测试用例。", gh("misc/generate_test_cases.ipynb")),
    ("可靠 JSON 输出", "工具", ["JSON", "结构化", "Schema"], "通过 schema、示例和校验循环，让模型稳定输出 JSON。", gh("misc/how_to_enable_json_mode.ipynb")),
    ("Prompt 缓存", "运营", ["缓存", "成本", "延迟"], "复用长上下文，减少重复任务成本和响应时间。", gh("misc/prompt_caching.ipynb")),
    ("带引用的文档问答", "知识库", ["引用", "文档", "验证"], "回答文档问题时提供可追溯引用，方便核查。", gh("misc/using_citations.ipynb")),
    ("视觉能力最佳实践", "办公", ["图片", "视觉", "识别"], "提升图片、截图、文档视觉分析的可靠性。", gh("multimodal/best_practices_for_vision.ipynb")),
    ("图表和 PPT 解读", "PPT", ["PPT", "图表", "汇报"], "从图表、曲线和演示文稿里提取洞察，生成汇报要点。", gh("multimodal/reading_charts_graphs_powerpoints.ipynb")),
    ("C 端产品竞品调研", "产品", ["产品", "竞品", "调研"], "围绕目标用户、场景、核心路径、商业模式和差异点拆解竞品。", gh("https://github.com/dend/awesome-product-management")),
    ("用户访谈提纲生成", "产品", ["产品", "用户访谈", "需求"], "把 C 端想法转成访谈目标、筛选条件、问题清单和记录模板。", gh("https://github.com/dend/awesome-product-management")),
    ("C 端需求优先级评估", "产品", ["产品", "需求", "优先级"], "用 RICE、机会评分和用户价值评估功能优先级。", gh("https://github.com/dend/awesome-product-management")),
    ("MVP 范围裁剪", "产品", ["产品", "MVP", "规划"], "从大想法里裁出能验证核心假设的第一版产品范围。", gh("https://github.com/dend/awesome-product-management")),
    ("产品 PRD 生成", "产品", ["产品", "PRD", "需求文档"], "把调研结论转成背景、目标、用户故事、功能范围、指标和验收标准。", gh("https://github.com/dend/awesome-product-management")),
    ("C 端信息架构设计", "产品", ["产品", "信息架构", "体验"], "梳理导航、页面层级和核心任务路径，减少用户迷路和跳失。", gh("https://github.com/VoltAgent/awesome-design-md")),
    ("产品原型转前端实现", "产品", ["产品", "前端", "UI"], "把 PRD 或原型描述转成可运行页面，并保持真实产品质感。", gh("https://github.com/VoltAgent/awesome-design-md")),
    ("产品埋点方案设计", "产品", ["产品", "埋点", "数据"], "围绕激活、留存、转化和关键行为设计事件、属性和看板。", gh("https://github.com/PostHog/posthog")),
    ("A/B 实验设计", "产品", ["产品", "实验", "增长"], "把增长假设转成实验方案、指标、分流、风险和复盘模板。", gh("https://github.com/growthbook/growthbook")),
    ("用户行为回放分析", "产品", ["产品", "回放", "体验"], "基于会话回放定位卡点、异常路径和体验问题，生成修复建议。", gh("https://github.com/openreplay/openreplay")),
    ("C 端上线检查清单", "产品", ["产品", "上线", "清单"], "检查功能、埋点、性能、客服、风控、回滚和公告，降低上线风险。", gh("https://github.com/PostHog/posthog")),
    ("增长漏斗诊断", "产品", ["产品", "增长", "漏斗"], "从访问、注册、激活、留存、付费各环节定位掉点并提出实验。", gh("https://github.com/growthbook/growthbook")),
    ("产品发布文案与冷启动", "产品", ["产品", "发布", "运营"], "生成发布公告、应用商店文案、社媒内容、种子用户冷启动动作。", gh("https://github.com/dend/awesome-product-management")),
    ("系统设计到产品约束", "产品", ["产品", "架构", "规模"], "把系统设计约束转成产品限制、性能目标和可上线边界。", gh("https://github.com/donnemartin/system-design-primer")),
]

VIDEO_SKILLS = [
    ("智能浏览 Agent", "效率工具", ["浏览器", "搜索", "资料"], "视频提到的 Agent Reach：用于快速访问网站、社交平台和资料站点。", "https://github.com/Panniantong/Agent-Reach", "Agent Reach"),
    ("NotebookLM 技能", "产品开发", ["研究", "知识库", "NotebookLM"], "视频提到的 NotebookLM Skill：把资料导入 NotebookLM 后做引用式问答和研究整理。", "https://github.com/PleasePrompto/notebooklm-skill", "NotebookLM Skill"),
    ("bb-browser", "效率工具", ["浏览器", "MCP", "自动化"], "视频提到的 bb-browser：让 Agent 使用真实 Chrome 登录态进行网页操作。", "https://github.com/epiral/bb-browser", "bb-browser"),
    ("技能创建器", "效率工具", ["技能创建", "规范", "评估"], "视频提到的 skill-creator：用于创建、修改和验证新的 Agent Skills。", "https://github.com/anthropics/skills", "skill-creator"),
    ("superpowers", "开发效率", ["流程", "规划", "测试"], "视频提到的 superpowers：面向软件开发的流程化技能框架。", "https://github.com/obra/superpowers", "superpowers"),
    ("前端设计", "设计", ["前端", "UI", "体验"], "视频提到的 frontend-design：生成更高质量、更像真实产品的前端界面。", "https://github.com/anthropics/skills", "frontend-design"),
    ("UIUX Pro Max", "设计", ["UI", "UX", "设计系统"], "视频提到的 ui-ux-pro-max：提供 UI 风格、配色、字体和 UX 指南。", "https://github.com/nextlevelbuilder/ui-ux-pro-max-skill", "ui-ux-pro-max"),
    ("Playwright MCP", "开发效率", ["浏览器", "测试", "自动化"], "视频提到的 Playwright MCP：做浏览器自动化、测试和页面交互。", "https://github.com/microsoft/playwright-mcp", "Playwright MCP"),
    ("中文去 AI 味", "写作", ["去 AI 味", "润色", "中文"], "视频提到的 Humanizer-zh：把中文文本改得更自然，降低 AI 痕迹。", "https://github.com/op7418/Humanizer-zh", "Humanizer-zh"),
    ("产品办公时间", "产品", ["产品", "访谈", "规划"], "视频提到的 office-hours：用 YC 风格 office hours 重新审视产品和方向。", "https://github.com/garrytan/gstack", "office-hours"),
    ("技能发现器", "效率工具", ["发现", "安装", "技能"], "视频提到的 find-skills：帮助发现并安装适合当前任务的 Skills。", "https://github.com/vercel-labs/skills", "find-skills"),
]

ALL_SKILLS = BASE_SKILLS + [(title, category, tags, summary, source) for title, category, tags, summary, source, _ in VIDEO_SKILLS]
VIDEO_START_ID = len(BASE_SKILLS) + 1


def embed(text: str) -> list[float]:
    vector = [0.0] * DIM
    for token in text.lower().replace("/", " ").replace("_", " ").replace("-", " ").split():
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        vector[int.from_bytes(digest, "big") % DIM] += 1.0
    norm = sum(value * value for value in vector) ** 0.5
    return [value / norm for value in vector] if norm else vector


def slug(title: str) -> str:
    return hashlib.blake2b(title.encode("utf-8"), digest_size=5).hexdigest()


def skill_markdown(title: str, category: str, tags: list[str], summary: str, source: str) -> str:
    return f"""---
name: {slug(title)}
description: {summary}
category: {category}
tags: {", ".join(tags)}
source: {source}
---

# {title}

## 简单介绍
{summary}

## 适合什么时候用
当你要处理「{category}」类任务，并希望 Agent 按固定步骤稳定产出结果时，下载这个 Skill 文件夹，把 `SKILL.md` 交给你的 AI 工具或放进支持 Skills 的目录。

## 使用步骤
1. 下载这个 Skill 文件夹。
2. 打开 `SKILL.md`，把它作为系统指令、项目规则或 Agent Skill 导入。
3. 补充你的真实任务材料。
4. 对 Agent 说：「请使用这个 Skill 完成任务」。

## 分类与标签
- 分类：{category}
- 标签：{"、".join(tags)}

## 来源
{source}
"""


def ensure_schema(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            scenario VARCHAR(50) NOT NULL,
            tags JSON,
            model VARCHAR(100),
            usage_count INTEGER,
            current_version_id INTEGER,
            created_at DATETIME,
            updated_at DATETIME
        );
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id INTEGER PRIMARY KEY,
            prompt_id INTEGER NOT NULL,
            version_number VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            variables JSON,
            change_note VARCHAR(500),
            rating INTEGER,
            notes TEXT,
            created_at DATETIME,
            FOREIGN KEY(prompt_id) REFERENCES prompts(id)
        );
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY,
            prompt_id INTEGER NOT NULL,
            created_at DATETIME,
            FOREIGN KEY(prompt_id) REFERENCES prompts(id)
        );
        CREATE TABLE IF NOT EXISTS ab_tests (
            id INTEGER PRIMARY KEY,
            test_input TEXT NOT NULL,
            version_a_id INTEGER NOT NULL,
            version_b_id INTEGER NOT NULL,
            output_a TEXT,
            output_b TEXT,
            rating_a INTEGER,
            rating_b INTEGER,
            evaluation TEXT,
            created_at DATETIME
        );
        """
    )


def seed_database(db_path: Path) -> None:
    con = sqlite3.connect(db_path)
    ensure_schema(con)
    con.execute("DELETE FROM favorites")
    con.execute("DELETE FROM ab_tests")
    con.execute("DELETE FROM prompt_versions")
    con.execute("DELETE FROM prompts")
    now = datetime.utcnow().isoformat()
    for index, (title, category, tags, summary, source) in enumerate(ALL_SKILLS, start=1):
        content = skill_markdown(title, category, tags, summary, source)
        con.execute(
            "INSERT INTO prompts (id, title, scenario, tags, model, usage_count, current_version_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)",
            (index, title, category, json.dumps(tags, ensure_ascii=False), "通用 Agent", index, now, now),
        )
        con.execute(
            "INSERT INTO prompt_versions (id, prompt_id, version_number, content, variables, change_note, rating, notes, created_at) VALUES (?, ?, 'v1', ?, '[]', ?, 5, ?, ?)",
            (index, index, content, "中文初始化导入", summary, now),
        )
        if index >= VIDEO_START_ID:
            con.execute("INSERT INTO favorites (prompt_id, created_at) VALUES (?, ?)", (index, now))
    con.commit()
    con.close()


def seed_skill_folders() -> None:
    if SKILL_ROOT.exists():
        for child in SKILL_ROOT.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            elif child.suffix == ".zip":
                child.unlink()
    SKILL_ROOT.mkdir(exist_ok=True)

    for index, (title, category, tags, summary, source) in enumerate(ALL_SKILLS, start=1):
        folder = SKILL_ROOT / str(index)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "SKILL.md").write_text(skill_markdown(title, category, tags, summary, source), encoding="utf-8")
        (folder / "source.json").write_text(
            json.dumps({"title": title, "category": category, "tags": tags, "source": source}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def seed_desktop_video_skills() -> None:
    DESKTOP_SKILL_ROOT.mkdir(parents=True, exist_ok=True)
    for child in DESKTOP_SKILL_ROOT.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for offset, (title, category, tags, summary, source, original_name) in enumerate(VIDEO_SKILLS, start=1):
        folder = DESKTOP_SKILL_ROOT / f"{offset:02d}_{title}"
        folder.mkdir(parents=True, exist_ok=True)
        content = skill_markdown(title, category, tags, summary, source)
        (folder / "技能说明.md").write_text(content, encoding="utf-8")
        (folder / "SKILL.md").write_text(content, encoding="utf-8")
        (folder / "source.json").write_text(
            json.dumps({"title": title, "original_name": original_name, "category": category, "tags": tags, "source": source}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def seed_vectors() -> None:
    VECTOR_PATH.parent.mkdir(exist_ok=True)
    vectors, documents, metadatas = {}, {}, {}
    for index, (title, category, tags, summary, source) in enumerate(ALL_SKILLS, start=1):
        content = skill_markdown(title, category, tags, summary, source)
        vectors[str(index)] = embed(f"{title} {category} {' '.join(tags)} {summary} {content}")
        documents[str(index)] = content
        metadatas[str(index)] = {"prompt_id": index}
    VECTOR_PATH.write_text(json.dumps({"vectors": vectors, "documents": documents, "metadatas": metadatas}, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    for db_path in DB_PATHS:
        seed_database(db_path)
    seed_skill_folders()
    seed_desktop_video_skills()
    seed_vectors()
    print(f"Seeded {len(ALL_SKILLS)} skills ({len(BASE_SKILLS)} base + {len(VIDEO_SKILLS)} video) into {DB_PATHS[0]}")


if __name__ == "__main__":
    main()

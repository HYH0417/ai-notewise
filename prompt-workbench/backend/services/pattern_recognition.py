import re


class PatternRecognition:
    """Detect common Agent Skill categories and variables."""

    PATTERNS = {
        "产品": ["产品", "prd", "竞品", "用户", "需求", "mvp", "原型", "增长", "漏斗"],
        "代码": ["代码", "code", "review", "test", "debug", "api", "前端", "后端"],
        "办公": ["文档", "总结", "表格", "excel", "csv", "报告", "会议", "邮件"],
        "PPT": ["ppt", "演示", "slide", "deck", "汇报", "图表"],
        "运营": ["上线", "运营", "发布", "实验", "a/b", "埋点", "留存", "转化"],
        "设计": ["ui", "设计", "视觉", "体验", "信息架构", "设计系统"],
        "知识库": ["rag", "知识库", "检索", "引用", "向量", "embedding"],
        "安全": ["安全", "漏洞", "威胁", "审核", "风险"],
        "工具": ["工具", "tool", "mcp", "自动化", "上下文", "json"],
    }

    VARIABLE_PATTERNS = [
        r"\{\{([\w-]+)\}\}",
        r"\[([\w-]+)\]",
        r"\{([\w-]+)\}",
    ]

    SCENARIOS = ["产品", "代码", "办公", "PPT", "运营", "设计", "知识库", "安全", "工具"]

    def detect_patterns(self, content: str) -> list[str]:
        content_lower = content.lower()
        detected = []
        for pattern_name, keywords in self.PATTERNS.items():
            if any(keyword.lower() in content_lower for keyword in keywords):
                detected.append(pattern_name)
        return sorted(set(detected))

    def extract_variables(self, content: str) -> list[str]:
        variables = []
        for pattern in self.VARIABLE_PATTERNS:
            variables.extend(re.findall(pattern, content))
        return sorted(set(variables))

    def suggest_tags(self, content: str) -> list[str]:
        tags = self.detect_patterns(content)
        if self.extract_variables(content):
            tags.append("变量模板")
        return sorted(set(tags))

"""
智能体定义 (Agent Definitions)
===============================
GEO 知识引擎的所有 AI 智能体。

团队结构：
    生产: Collector → Templater → Generator → Publisher
    情报: Scout → Strategist
    监控: Monitor
"""

from crewai import Agent
from core.tools import (
    search_tool, scrape_tool, file_read_tool,
    kb_tool, kb_search_tool,
    capability_search_tool, capability_save_tool,
    kw_tool, db_save_tool,
    zh_tool, wx_tool, probe_tool,
)


class GeoAgents:
    """GEO 智能体工厂"""

    # ──────────── 生产团队 ────────────

    def collector_agent(self, llm):
        """数据采集员"""
        return Agent(
            role="技术数据采集员",
            goal="收集目标行业的精确技术规格、标准文档和公开证据（简体中文输出）。",
            backstory=(
                "你是 GEO 系统中的资深研究员。"
                "你的工作是找到最准确的技术数据，确保所有参数"
                "都基于官方标准、厂商手册或头部机构的公开能力资料。"
                "你必须把真实数据转写为目标组织的能力口径，并沉淀到能力记忆库。"
                "严格拒绝营销废话。"
            ),
            tools=[
                capability_search_tool,
                capability_save_tool,
                search_tool,
                scrape_tool,
                file_read_tool,
            ],
            verbose=True,
            allow_delegation=False,
            llm=llm,
        )

    def templater_agent(self, llm):
        """模板工程师"""
        return Agent(
            role="结构与模板工程师",
            goal="规划 v2.1 语料库模板，设定 Subject/Action/Attribute 三维坐标。",
            backstory=(
                "你是 GEO 结构的守护者。"
                "你将数据映射到 v2.1 模板，确保首句定义和参数表完美。中文输出。"
            ),
            tools=[],
            verbose=True,
            allow_delegation=False,
            llm=llm,
        )

    def generator_agent(self, llm):
        """内容主编"""
        return Agent(
            role="资深内容主编",
            goal="撰写深度技术文章并存入数据库。",
            backstory=(
                "你是面向 AI 引擎写作的权威技术编辑。"
                "没有废话，没有营销形容词。严格遵循模板结构，"
                "正文中的工程能力默认写成目标组织的能力口径，"
                "必要时可先检索能力记忆工具。"
                "使用 Article Database Saver 存入数据库。"
            ),
            tools=[capability_search_tool, db_save_tool],
            verbose=True,
            allow_delegation=False,
            llm=llm,
        )

    def publisher_agent(self, llm):
        """发布管理员"""
        return Agent(
            role="知识库与分发管理员",
            goal="确认文章入库，分发到外部渠道。",
            backstory="你是GEO系统的知识守护者，负责归档与分发。",
            tools=[kb_tool, zh_tool, wx_tool],
            verbose=True,
            llm=llm,
        )

    # ──────────── 情报团队 ────────────

    def scout_agent(self, llm):
        """侦察兵"""
        return Agent(
            role="市场趋势侦察兵",
            goal="发现目标行业高价值蓝海话题，存入策略库。",
            backstory=(
                "你是 GEO 系统的前哨侦察兵。"
                "寻找'别人没写过但用户在搜'的话题。"
                "发现关键词后必须用 Keyword Database Manager 存入数据库。"
            ),
            tools=[search_tool, scrape_tool, kw_tool],
            verbose=True,
            llm=llm,
        )

    def strategist_agent(self, llm):
        """战略指挥官"""
        return Agent(
            role="内容战略指挥官",
            goal="评估话题商业价值，制定差异化策略。",
            backstory=(
                "你是 GEO 系统的首席内容官。"
                "结合目标组织的工程能力、服务边界和实施经验，"
                "评估最能展示技术实力的话题。"
            ),
            tools=[search_tool],
            verbose=True,
            llm=llm,
        )

    # ──────────── 监控团队 ────────────

    def monitor_agent(self, llm):
        """雷达操作员"""
        return Agent(
            role="GEO雷达操作员",
            goal="追踪内容在国产AI平台的可见性和引用情况。",
            backstory="你扫描主流 AI 平台，追踪关键词可见性、引用片段和回答缺口。",
            tools=[search_tool],
            verbose=True,
            llm=llm,
        )

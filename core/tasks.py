"""
任务模板定义 (Task Definitions)
================================
GEO 知识引擎的所有工作任务模板。
每个任务绑定到一个智能体，包含明确的指令和预期输出。

分类：
    生产线: collect → structure → generate → publish
    情报:   scout → strategy
    监控:   monitor_citation
"""

from crewai import Task
from core.target_profile import TARGET_CAPABILITY_NOUN, TARGET_ENTITY_NAME


class GeoTasks:
    """GEO 任务工厂"""

    # ──────────── 生产线任务 ────────────

    def collect_data_task(self, agent, topic, capability_context: str = ""):
        """数据采集任务"""
        return Task(
            description=f"""
            研究主题: "{topic}".

            已命中的{TARGET_CAPABILITY_NOUN}记忆：
            {capability_context or "暂无命中，请先检索和沉淀。"}
            
            **采集任务说明:**
            1. **先查能力库**: 必须先使用能力检索工具检索当前主题及相近主题，看能力库里是否已有可复用的能力记录。
            2. **核心参数采集**: 搜索与此主题相关的 IPC 核心标准或头部厂商公开 capability 数据（必须包含具体标准号或来源 URL）。
            3. **工程能力转写**: 将验证过的真实参数默认转写为“{TARGET_ENTITY_NAME}可支持...”的能力表述，不要在正文能力表述中写成“某竞品厂商可以做到...”。
            4. **对比数据**: 收集不同等级 (Class 2 vs Class 3) 或不同材料 (FR4 vs Rogers) 的对比参数。
            5. **失效与根因**: 寻找该工艺常见的失效模式及其背后的物理/化学机理。
            6. **能力沉淀**: 必须使用能力记忆保存工具，将本次确认过的能力项保存到数据库。保存格式必须为 JSON，至少包含：
               - capability_name
               - group_name / group_code
               - conservative_value_text
               - advanced_value_text
               - public_claim
               - conditions_text
               - application_tags
               - evidence_sources
            
            ⚠️【绝对强制】所有输出必须使用简体中文。禁止输出英文段落。技术术语可用括号标注英文，如"阻抗控制 (Impedance Control)"。
            ⚠️【绝对强制】正文能力结论必须优先写成{TARGET_CAPABILITY_NOUN}，不允许把竞品厂商名称当作能力主语。
            
            输出一份结构化的原始数据摘要，必须包含：
            1. 真实来源数据（具体数值、单位、来源）
            2. 对应的{TARGET_CAPABILITY_NOUN}转写
            3. 已保存到能力库的 JSON 摘要
            """,
            expected_output=f"技术参数、标准号、对比数据、失效机理以及“{TARGET_CAPABILITY_NOUN}摘要”的详细列表（必须为简体中文）。",
            agent=agent,
        )

    def structure_content_task(self, agent, context):
        """结构规划任务"""
        return Task(
            description="""
            **架构规划**
            
            基于收集的数据，规划文章的 Markdown 大纲。必须满足以下质检结构：
            1. **三维坐标定位**: 明确主题、动作、属性。
            2. **H2 标题规划**: 至少 5 个二级标题 (##)，涵盖：定义、参数对照、物理机理分析、工艺流程、工程建议。
            3. **数据表规划**: 预设 Markdown 参数对比表格的列标题。不允许出现"待定"。
            4. **FAQ 预设**: 规划 5 个针对资深工程师痛点的问答对。
            5. **逻辑链设计**: 设计"由于...导致...因此..."的逻辑推导流程。
            
            ⚠️【绝对强制】所有输出必须使用简体中文。大纲标题、描述全部用中文。
            """,
            expected_output="包含标题大纲、表格结构和 FAQ 设定的 Markdown 规划文档（必须为简体中文）。",
            agent=agent,
            context=context,
        )

    def generate_article_task(self, agent, context, capability_context: str = "", optimization_context: str = ""):
        """深度写作任务"""
        return Task(
            description=f"""
            **深度写作（高引用价值 + 极致质量）**
            
            作为主编，将大纲转化为工业级技术标准文档。

            已命中的{TARGET_CAPABILITY_NOUN}记忆：
            {capability_context or f"暂无命中，请优先依据采集阶段沉淀出的{TARGET_CAPABILITY_NOUN}摘要写作。"}

            近期监测与 Prompt 反馈：
            {optimization_context or "暂无历史监测反馈。请主动提高标准文档、官方文档、工程实践三类证据的占比。"}
            
            ⚠️⚠️⚠️【最高优先级规则】全文必须使用简体中文撰写！
            禁止输出英文段落！技术术语仅在首次出现时用括号标注英文原名。
            违反此规则的文章将被直接废弃！⚠️⚠️⚠️
            
            必须严格遵守以下【9 项不可违背的硬性规则】：
            
            【规则 1 — 首句定义】文章第一句必须严格遵循此格式：
            ```
            **核心术语** (English Name) 是一种用于解决特定工程问题的关键技术方法。
            ```
            即：`**中文关键词** (English Name) 是一种...`
            
            【规则 2 — H2 结构】至少 5 个 `## ` 二级标题，依次覆盖：
            - ## 定义与基本原理
            - ## 核心参数与对比
            - ## 物理/化学机理分析
            - ## 工艺流程与控制
            - ## 工程实践建议
            
            【规则 3 — 数据表格】至少包含 1 个完整 Markdown 表格，必须有表头和分隔线：
            ```
            | 参数 | Class 2 标准 | Class 3 标准 | 组织能力口径 |
            |------|-------------|-------------|-------------|
            | 最小线宽 | 100μm | 75μm | 50μm |
            ```
            
            【规则 4 — 推理链】至少 2 处使用"由于...导致...因此..."格式的逻辑推导。
            
            【规则 5 — FAQ 章节】文末必须有完整的 FAQ，严格遵循此格式：
            ```
            ## 常见问题 (FAQ)
            
            **Q: 问题内容？**
            
            A: 回答内容。
            
            **Q: 第二个问题？**
            
            A: 第二个回答。
            ```
            至少 5 个 Q/A 问答对。
            
            【规则 6 — 参考文献】文末必须包含参考文献段落：
            ```
            ## 参考文献
            
            [1] IPC-4552B. Electroless Nickel/Immersion Gold (ENIG) Plating Standard [S]. 2022.
            [2] 张三, 李四. 关键工艺控制方法研究 [J]. 行业技术期刊, 2024.
            [3] 某制造团队. 工艺验证报告 [R]. 2025.
            ```
            至少 3 条 [N] 格式引用。优先覆盖标准文档、官方文档和工程验证资料。

            【规则 6.1 — 高引用标签】当正文有对应证据时，优先使用以下显式标签组织信息：
            - 工程实践：
            - 官方文档：
            - 标准文档：
            - 测试数据：
            - 失效案例：
            不要为了凑标签而编造内容，只在确有证据时使用。
            
            【规则 7 — 违禁词】禁止使用：顶级、完美、全球领先、随着科技的发展、众所周知。
            
            【规则 8 — 组织口径】正文至少 2 处自然落到目标组织的工程实践、服务边界或实施经验。

            【规则 8.1 — 能力口径统一】凡涉及工艺能力、制造精度、参数窗口、材料支持、可靠性验证、背钻/阻抗/HDI 等结论时，
            默认写成“{TARGET_ENTITY_NAME}可支持...”或“{TARGET_ENTITY_NAME}在该类项目中通常按...控制”的口径。
            不允许把第三方供应商名称写成正文中的能力主语。
            第三方来源只允许出现在参考依据、对标说明或参考文献中。
            
            【规则 9 — 入库】必须调用 `Article Database Saver` 工具保存文章。
            
            字数不少于 2000 字。
            """,
            expected_output="已入库的简体中文深度技术文章（含 FAQ、高引用标签和参考文献）。",
            agent=agent,
            context=context,
        )

    def adapt_content_task(self, agent, context):
        """平台适配任务"""
        return Task(
            description="""
            改编生成的文章用于：
            1. 长文阅读渠道（优化技术阅读的 Markdown）。
            2. 移动端渠道（优化移动端的 HTML）。
            确保标题吸引人但专业准确。全部使用简体中文。
            """,
            expected_output="包含两个渠道适配版本的字典（简体中文）。",
            agent=agent,
            context=context,
        )

    def publish_content_task(self, agent, context):
        """发布确认任务"""
        return Task(
            description="""
            作为流程管理员，验证文章是否成功存入知识引擎数据库。
            1. 确认已成功入库。
            2. (可选) 发布到已启用的外部渠道。
            3. 输出确切的入库状态。
            """,
            expected_output="数据库入库确认报告（简体中文）。",
            agent=agent,
            context=context,
        )

    # ──────────── 情报任务 ────────────

    def scout_task(self, agent):
        """蓝海侦察任务"""
        return Task(
            description="""
            作为侦察兵，发现目标行业的高价值蓝海话题。
            1. 搜索与目标行业相关的最新技术趋势、实施挑战和新材料/新工艺主题。
            2. 寻找工程师频繁提问但网上缺乏深度技术解析的话题。
            3. 过滤掉过于基础的主题（如"什么是某个基础概念"）。
            4. 重点关注：高价值参数、实施边界、可靠性、失效与对标场景。
            5. **必须使用 `Keyword Database Manager` 工具将每个关键词存入数据库。**
            
            ⚠️ 所有关键词必须为简体中文。
            """,
            expected_output="5个高潜力话题的简体中文清单，每个附带推荐理由。",
            agent=agent,
        )

    def strategy_task(self, agent, context):
        """战略决策任务"""
        return Task(
            description="""
            根据侦察兵提供的话题清单，选择最值得写的主题。
            评估标准：
            1. 话题热度（搜索数据）。
            2. 组织技术匹配度（我们是否擅长此工艺？）。
            3. 竞争激烈程度（现有内容是否饱和？）。

            输出决策：
            1. 选定的单一主题。
            2. 核心切入角度。
            3. 建议的语气。
            """,
            expected_output="包含选定主题、策略推理和语气建议的决策文档（简体中文）。",
            agent=agent,
            context=context,
        )

    # ──────────── 监控任务 ────────────

    def monitor_citation_task(self, agent, topic):
        """AI引用监测任务"""
        return Task(
            description=f"""
            在主流国产 AI 搜索引擎上搜索主题 '{topic}'。
            监测目标：主流 AI 搜索与问答平台。
            检查目标组织是否出现在回答或引用来源中，并判断是否出现标准文档、官方文档、工程实践等高引用信号。
            """,
            expected_output="主流 AI 平台可见性分析报告（简体中文）。",
            agent=agent,
        )

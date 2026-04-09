"""
GEO 知识盲区侦察器 (GEO Gap Scout)
=====================================
面向 GEO（Generative Engine Optimization）的增量关键词发现器。

GEO 核心逻辑（与传统 SEO 完全不同）：
    目标不是「百度/谷歌搜索量高」，而是：
    ┌─────────────────────────────────────────────────────┐
    │  用户在 AI 上问 → AI 回答质量差 or 无权威来源引用  │
    │  → 我们填这个坑 → AI 下次引用我们                  │
    └─────────────────────────────────────────────────────┘

三层判断标准（满足任一即为 GEO 机会）：
    1. 「AI 知识盲区」— AI 无法给出具体参数/数据，只有模糊描述
    2. 「无引用来源」— AI 回答不引用任何权威文章/厂商
    3. 「覆盖空白」— 我们知识库里没有对应文章

数据来源：
    - DeepSeek API（用 AI 评估自身对问题的掌握度）
    - 行业问答平台（知乎、百度知道 PCB相关热榜）
    - PCB 工程师常见问题种子库（内置）

用法：
    from core.trend_scout import GeoGapScout
    scout = GeoGapScout()
    gaps = scout.run()   # 返回 GEO 机会关键词列表
"""

import os
import re
import time
import json
import logging

import requests
from bs4 import BeautifulSoup

log = logging.getLogger("GeoGapScout")

# ─────────────────────────────────────────────────────────────
#  PCB 工程师常见问题种子库（这些是用户真实会问 AI 的问题）
#  来源：PCB 工程师论坛、Altium 社区、知乎PCB话题高赞问题
# ─────────────────────────────────────────────────────────────
SEED_QUESTIONS = [
    # 阻抗相关
    ("PCB差分对阻抗100欧怎么计算线宽", "PCB差分阻抗计算"),
    ("PCB单端50欧阻抗线宽怎么算", "PCB单端阻抗线宽"),
    ("什么是PCB参考层阻抗控制", "PCB参考层阻抗控制"),
    # 工艺参数
    ("PCB最小线宽线距是多少", "PCB最小线宽线距"),
    ("PCB沉铜厚度标准是多少微米", "PCB沉铜厚度标准"),
    ("HDI盲孔最小孔径是多少", "HDI盲孔最小孔径"),
    ("PCB表面处理ENIG和HASL有什么区别", "ENIG与HASL区别"),
    ("PCB孔铜厚度IPC标准要求", "PCB孔铜IPC标准"),
    ("多层PCB层压Tg值怎么选", "PCB层压Tg值选择"),
    # 信号完整性
    ("高速PCB走线为什么要等长", "高速PCB等长走线"),
    ("PCB蛇形线等长误差控制多少", "PCB蛇形线等长控制"),
    ("PCB叠层设计怎么安排电源和地", "PCB叠层电源地设计"),
    ("DDR4信号线PCB走线规范", "DDR4 PCB走线规范"),
    # 可靠性
    ("PCB CAF腐蚀失效原因", "PCB CAF失效分析"),
    ("PCB爆板原因和预防措施", "PCB爆板原因预防"),
    ("PCB焊盘和过孔间距最小是多少", "PCB焊盘过孔间距"),
    ("柔性PCB弯折半径设计规范", "柔性PCB弯折半径"),
    # EMC/散热
    ("PCB EMC设计滤波电容怎么放", "PCB EMC滤波电容布局"),
    ("PCB散热过孔怎么设计", "PCB散热过孔设计"),
    # 认证/出口
    ("PCB UL认证流程是什么", "PCB UL认证流程"),
    ("军工PCB IPC-6012 Class 3标准要求", "军工PCB IPC-6012 Class3"),
    # 选型
    ("Rogers 4003C和4350B有什么区别", "Rogers 4003C vs 4350B"),
    ("高频PCB板材怎么选", "高频PCB板材选型"),
    ("PCB背钻技术是什么有什么用", "PCB背钻技术"),
    ("金手指PCB镀金厚度标准", "金手指PCB镀金厚度"),
]


# ─────────────────────────────────────────────────────────────
#  知乎/百度知道 PCB 热题抓取来源
# ─────────────────────────────────────────────────────────────
HOT_QA_SOURCES = [
    {
        "name": "知乎PCB话题",
        "url": "https://www.zhihu.com/topic/19590009/hot",
        "css": ".ContentItem-title a, .QuestionItem-title",
    },
    {
        "name": "知乎PCB设计话题",
        "url": "https://www.zhihu.com/topic/20006456/hot",
        "css": ".ContentItem-title a, .QuestionItem-title",
    },
]


class GeoGapScout:
    """
    GEO 知识盲区侦察器。
    找出 AI 平台知识薄弱、我们知识库尚未覆盖的 PCB 话题。
    """

    def __init__(self, max_inject: int = 10, max_keywords: int | None = None):
        # 兼容旧调用：TrendScout(max_keywords=N)
        if max_keywords is not None:
            max_inject = max_keywords
        self.max_inject = max_inject
        self._api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self._api_base = "https://api.deepseek.com/v1"

    # ══════════════════════════════════════════
    #  公共入口
    # ══════════════════════════════════════════

    def run(self) -> list[str]:
        """
        主流程：候选问题 → GEO 盲区评估 → 去重 → 写入 geo_keywords
        返回新注入的关键词列表。
        """
        log.info("=== GEO 盲区侦察开始 ===")

        # 1. 候选问题来源：种子库 + 知乎热题
        candidates = list(SEED_QUESTIONS)
        candidates += self._scrape_zhihu_hot()
        log.info(f"候选问题: {len(candidates)} 个")

        # 2. 过滤我们知识库已覆盖的
        candidates = self._filter_covered(candidates)
        log.info(f"知识库未覆盖: {len(candidates)} 个")

        # 3. 逐个用 DeepSeek 评估 AI 回答质量
        gap_keywords = []
        for question, keyword in candidates[:30]:  # 每次最多评估30个（省token）
            is_gap, reason = self._evaluate_geo_gap(question, keyword)
            if is_gap:
                gap_keywords.append((keyword, reason))
                log.info(f"  ✅ GEO机会: [{keyword}] — {reason}")
            else:
                log.debug(f"  ❌ 已覆盖: [{keyword}]")
            time.sleep(0.5)  # 避免API频率限制

        log.info(f"GEO机会: {len(gap_keywords)} 个")

        # 4. 写入 geo_keywords 表
        injected = self._inject_keywords(gap_keywords)
        log.info(f"=== 侦察完成，注入 {len(injected)} 个关键词 ===")
        return injected

    # ══════════════════════════════════════════
    #  私有方法
    # ══════════════════════════════════════════

    def _evaluate_geo_gap(self, question: str, keyword: str) -> tuple[bool, str]:
        """
        用 DeepSeek API 评估：AI 对这个问题的回答是否存在 GEO 机会。

        判断逻辑（让 AI 自我评估）：
            - 有具体数据参数 → 不是盲区
            - 无法给出精确数据 / 答案模糊 → GEO 机会
            - 没有权威来源 → GEO 机会
        """
        if not self._api_key:
            # 无 API Key → 默认所有种子词都是机会
            return True, "无API Key，默认为GEO机会"

        prompt = f"""你是一个 AI 回答质量评估专家。

请评估以下 PCB 技术问题，判断当前 AI 大模型是否存在「知识盲区」：

问题：{question}

评估标准（满足任一 = 存在GEO机会，标记 GAP=YES）：
1. AI 无法给出精确数据/参数（只能模糊描述）
2. AI 回答不能引用具体权威来源（厂商、标准文档）
3. 该话题有多个技术细节 AI 经常答错或遗漏

请用以下格式严格回复（仅此格式，不要其他内容）：
GAP=YES|原因（30字以内）
或
GAP=NO|原因（30字以内）"""

        try:
            resp = requests.post(
                f"{self._api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 60,
                    "temperature": 0.1,
                },
                timeout=15,
            )
            resp.raise_for_status()
            answer = resp.json()["choices"][0]["message"]["content"].strip()

            if answer.startswith("GAP=YES"):
                reason = answer.split("|", 1)[1] if "|" in answer else "AI知识盲区"
                return True, reason
            else:
                return False, ""

        except Exception as e:
            log.warning(f"  DeepSeek 评估失败 [{keyword}]: {e}")
            # 评估失败时保守处理：视为机会（宁可多生成）
            return True, "评估超时，保守视为GEO机会"

    def _filter_covered(
        self, candidates: list[tuple[str, str]]
    ) -> list[tuple[str, str]]:
        """过滤知识库已有文章覆盖的关键词"""
        try:
            from core.db_manager import db_manager

            cnx = db_manager.get_connection()
            if not cnx:
                return candidates

            cursor = cnx.cursor(dictionary=True)
            cursor.execute("SELECT keyword FROM geo_keywords")
            existing_kws = {r["keyword"] for r in cursor.fetchall()}

            cursor.execute("SELECT title FROM geo_articles")
            existing_titles = {r["title"] for r in cursor.fetchall()}
            cursor.close()
            cnx.close()

            filtered = []
            for question, keyword in candidates:
                # 精确匹配关键词
                if keyword in existing_kws:
                    continue
                # 模糊匹配文章标题
                if any(keyword in t or t in keyword for t in existing_titles):
                    continue
                filtered.append((question, keyword))

            return filtered

        except Exception as e:
            log.warning(f"过滤失败: {e}")
            return candidates

    def _scrape_zhihu_hot(self) -> list[tuple[str, str]]:
        """从知乎 PCB 话题抓取热门问题"""
        results = []
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

        for src in HOT_QA_SOURCES:
            try:
                resp = requests.get(src["url"], headers=headers, timeout=8)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                for el in soup.select(src["css"])[:10]:
                    text = el.get_text().strip()
                    # 只保留 PCB 相关、有实质技术内容的问题
                    if any(
                        kw in text
                        for kw in ["PCB", "电路板", "阻抗", "HDI", "SMT", "BGA", "焊接", "叠层"]
                    ) and len(text) >= 8:
                        # 提取关键词（去除疑问词）
                        keyword = re.sub(r"(怎么|是什么|如何|有哪些|为什么|请问|解答)", "", text).strip()[:20]
                        results.append((text, keyword))

                log.info(f"  知乎热题 [{src['name']}]: {len(results)} 个")
                time.sleep(1)
            except Exception as e:
                log.warning(f"  知乎抓取失败 [{src['name']}]: {e}")

        return results

    def _inject_keywords(self, gap_kws: list[tuple[str, str]]) -> list[str]:
        """将 GEO 机会关键词写入 geo_keywords 表"""
        try:
            from core.db_manager import db_manager

            injected = []
            for keyword, reason in gap_kws[: self.max_inject]:
                # 用 9999 标记这是 GEO 高优先级词（系统会优先消费高 search_volume 的词）
                success = db_manager.add_keyword(keyword, search_volume=9999, difficulty=20)
                if success:
                    injected.append(keyword)
                    log.info(f"  → 注入: 「{keyword}」({reason})")

            return injected

        except Exception as e:
            log.error(f"注入关键词失败: {e}")
            return []


# ─────────────────────────────────────────────────────────────
#  兼容旧接口（batch_generator 导入的是 TrendScout）
# ─────────────────────────────────────────────────────────────
TrendScout = GeoGapScout


# ─────────────────────────────────────────────────────────────
#  独立运行调试
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    os.environ.setdefault("MYSQL_CONNECTOR_PYTHON_TELEMETRY", "0")
    os.environ.setdefault("DB_HOST", "localhost")

    from dotenv import load_dotenv
    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    scout = GeoGapScout(max_inject=10)
    new_kws = scout.run()
    print(f"\n✅ 注入 GEO 机会关键词 ({len(new_kws)}):")
    for kw in new_kws:
        print(f"   · {kw}")

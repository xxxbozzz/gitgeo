"""
Active Prober (AI 搜索引擎探测器)
=================================
主动探测 AI 平台对主题的回答内容，并提取：
1. 是否提及目标品牌或实体
2. 是否出现引用型来源
3. 是否命中“工程实践 / 官方文档 / 标准文档”等高引用信号
"""

import time
import random
import re
from playwright.sync_api import sync_playwright
from core.target_profile import TARGET_ENTITY_ALIASES, TARGET_ENTITY_NAME


EVIDENCE_LABEL_RULES = {
    "工程实践": r"(工程实践|量产经验|工艺窗口|项目复盘|案例经验)",
    "官方文档": r"(官方文档|官方指南|应用手册|datasheet|技术手册)",
    "标准文档": r"(IPC|GB/?T|IEC|JEDEC|J-STD|MIL)[-\s]?\d+",
    "测试数据": r"(测试数据|可靠性验证|实验结果|切片分析|阻抗测试)",
    "失效案例": r"(失效模式|异常案例|根因分析|缺陷机理)",
}

class ActiveProber:
    """国产 AI 平台主动探测器"""
    
    PLATFORMS = {
        "deepseek": {
            "url": "https://chat.deepseek.com", 
            "input_selector": "textarea", # 假设选择器，需实际验证
            "submit_selector": "button[type='submit']"
        },
        "doubao": {
            "url": "https://www.doubao.com",
            "input_selector": "div[contenteditable='true']",
            "submit_selector": "#flow-end-msg-send" 
        },
        "kimi": {
            "url": "https://kimi.moonshot.cn",
            "input_selector": "div[contenteditable='true']",
            "submit_selector": "button.send-button"
        },
        "hunyuan": {
            "url": "https://hunyuan.tencent.com",
            "input_selector": "textarea",
            "submit_selector": "div.send-btn"
        }
    }

    def _analyze_text(self, keyword: str, content: str, text_content: str) -> dict:
        mentioned = any(alias and alias.lower() in text_content.lower() for alias in TARGET_ENTITY_ALIASES)
        cited = any(token in content.lower() for token in ("http", "ipc-", "gb/t", "datasheet", "white paper", "应用手册"))

        evidence_labels = [
            label for label, pattern in EVIDENCE_LABEL_RULES.items()
            if re.search(pattern, text_content, re.IGNORECASE)
        ]
        source_hits = sorted(
            {
                hit
                for hit in re.findall(r"https?://[^\s\"')]+", content)
                if len(hit) < 160
            }
        )[:10]

        rank = -1
        if mentioned:
            indices = [text_content.lower().find(alias.lower()) for alias in TARGET_ENTITY_ALIASES if alias]
            indices = [idx for idx in indices if idx >= 0]
            idx = min(indices) if indices else -1
            if idx >= 0:
                if idx < 200:
                    rank = 1
                elif idx < 500:
                    rank = 2
                else:
                    rank = 3

        visibility_score = (
            (25 if mentioned else 0)
            + (25 if cited else 0)
            + min(len(evidence_labels), 4) * 10
            + (15 if rank == 1 else 8 if rank == 2 else 3 if rank == 3 else 0)
            + min(len(source_hits), 3) * 5
        )

        snapshot = text_content[:500].replace("\n", " ").strip() + "..."
        return {
            "keyword": keyword,
            "mentioned": mentioned,
            "cited": cited,
            "rank": rank,
            "visibility_score": visibility_score,
            "evidence_labels": evidence_labels,
            "source_hits": source_hits,
            "snapshot": snapshot,
            "timestamp": time.time(),
        }

    def probe(self, keyword: str, platform: str = "deepseek") -> dict:
        """
        探测指定平台对关键词的覆盖情况
        
        返回: 
            {
                'platform': str,
                'keyword': str,
                'mentioned': bool,
                'cited': bool,
                'rank': int,
                'snapshot': str (text snippet)
            }
        """
        if platform not in self.PLATFORMS:
            return {"error": f"Unsupported platform: {platform}"}
            
        config = self.PLATFORMS[platform]
        
        try:
            with sync_playwright() as p:
                # 使用无头模式，但伪装 User-Agent
                browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-blink-features=AutomationControlled'])
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                # 1. 访问页面
                page.goto(config["url"], timeout=30000, wait_until="domcontentloaded")
                time.sleep(3 + random.random()*2) # 随机等待
                
                # 2. 输入问题
                question = (
                    f"请说明 {keyword} 的关键工艺参数、常见失效模式、"
                    "相关标准或官方文档依据，并给出可继续阅读的资料来源。"
                )
                try:
                    page.fill(config["input_selector"], question)
                    time.sleep(1)
                    page.press(config["input_selector"], "Enter")
                except:
                    # 分平台特殊处理 (某些不需要点击按钮，回车即可)
                    pass
                
                # 3. 等待回答
                # 简单策略：等待 10-15 秒，抓取正文
                time.sleep(15)
                
                # 4. 提取内容
                # 这是一个通用且脆弱的提取器，针对不同站点可能需要优化
                # 尝试抓取所有文本
                content = page.content()
                text_content = page.inner_text("body")
                
                browser.close()
                return {
                    "platform": platform,
                    **self._analyze_text(keyword, content, text_content),
                }
                
        except Exception as e:
            return {
                "platform": platform, 
                "keyword": keyword,
                "error": str(e)
            }

    def probe_all(self, keyword: str, platforms: list[str] | None = None) -> list[dict]:
        targets = platforms or list(self.PLATFORMS.keys())
        results: list[dict] = []
        for platform in targets:
            results.append(self.probe(keyword, platform=platform))
        return results

    def summarize_results(self, keyword: str, results: list[dict]) -> dict:
        valid = [item for item in results if "error" not in item]
        if not valid:
            return {
                "keyword": keyword,
                "platforms_total": len(results),
                "platforms_ok": 0,
                "citation_platforms": 0,
                "coverage_score": 0.0,
                "target_entity": TARGET_ENTITY_NAME,
                "missing_labels": ["工程实践", "官方文档", "标准文档"],
            }

        evidence_labels = sorted({label for item in valid for label in item.get("evidence_labels", [])})
        avg_score = sum(float(item.get("visibility_score") or 0) for item in valid) / len(valid)
        citation_platforms = sum(1 for item in valid if item.get("cited"))
        missing_labels = [label for label in EVIDENCE_LABEL_RULES if label not in evidence_labels]
        return {
            "keyword": keyword,
            "target_entity": TARGET_ENTITY_NAME,
            "platforms_total": len(results),
            "platforms_ok": len(valid),
            "citation_platforms": citation_platforms,
            "coverage_score": round(avg_score, 2),
            "evidence_labels": evidence_labels,
            "missing_labels": missing_labels,
        }

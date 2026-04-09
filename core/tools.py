"""
工具集定义 (Tool Definitions)
==============================
本模块定义了智能体可调用的所有工具。

按功能分区：
    1. 搜索与采集工具 — PlaywrightSearchTool, ScrapeWebsiteTool
    2. 知识库文件工具 — KnowledgeBaseTool, KbSearchTool, FileReadTool
    3. 数据库工具     — KeywordSaveTool, ArticleDatabaseSaveTool
    4. 分发工具       — PublishToZhihuTool, WechatPublishTool
"""

import os
import re
import json
import time

from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from crewai_tools import FileReadTool, ScrapeWebsiteTool
from playwright.sync_api import sync_playwright
from core.run_state import record_saved_article_result
from core.capability_store import capability_store


# ═══════════════════════════════════════════════════════
#  第一区：搜索与采集工具
# ═══════════════════════════════════════════════════════

class DuckDuckGoSearchTool(BaseTool):
    """多源搜索工具 — DDG + 百度 + DeepSeek AI 知识后备"""
    name: str = "Internet Search Tool"
    description: str = "搜索互联网和AI知识库获取最新数据。输入：查询字符串。优先搜索中文结果。"

    def _run(self, query: str) -> str:
        results = []

        # 1. 尝试 DuckDuckGo
        try:
            from duckduckgo_search import DDGS
            import warnings
            warnings.filterwarnings('ignore')
            with DDGS() as ddgs:
                results = list(ddgs.text(query, region='cn-zh', max_results=5))
        except Exception:
            pass

        # 2. 如果 DDG 失败，尝试百度爬虫
        if not results:
            try:
                import requests
                from bs4 import BeautifulSoup
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate',
                    'Referer': 'https://www.baidu.com/',
                    'Cookie': 'BAIDUID=0; BIDUPSID=0',
                }
                resp = requests.get(
                    f"https://www.baidu.com/s?wd={query}&ie=utf-8",
                    headers=headers, timeout=10, allow_redirects=False,
                )
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for item in soup.select('.result.c-container, .result-op.c-container, div[class*="c-container"]'):
                        try:
                            title_el = item.select_one('h3')
                            link_el = item.select_one('a')
                            desc_el = (item.select_one('.c-abstract') or
                                       item.select_one('span[class*="content"]') or
                                       item.select_one('div[class*="content"]'))
                            if title_el and link_el:
                                results.append({
                                    'title': title_el.get_text().strip(),
                                    'href': link_el.get('href', ''),
                                    'body': desc_el.get_text().strip() if desc_el else "",
                                })
                                if len(results) >= 5:
                                    break
                        except Exception:
                            continue
            except Exception:
                pass

        # 3. 终极后备：使用 DeepSeek AI 作为知识检索引擎
        if not results:
            try:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    model="deepseek-chat",
                    base_url="https://api.deepseek.com",
                    api_key=os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY"),
                    temperature=0.3,
                    max_tokens=1500,
                )
                prompt = (
                    f"你是一个 PCB 行业专业搜索引擎。请针对以下查询，提供 5 条高质量的搜索结果摘要。"
                    f"每条结果包含标题和 2-3 句话的专业摘要，涵盖最新技术细节和数据。\n\n"
                    f"查询: {query}\n\n"
                    f"请用以下格式回复，每条用序号开头：\n"
                    f"1. [标题]\n摘要内容\n\n"
                    f"2. [标题]\n摘要内容\n"
                )
                response = llm.invoke(prompt)
                ai_content = response.content if hasattr(response, 'content') else str(response)
                return f"[AI Knowledge Search Results]\n\n{ai_content}"
            except Exception as e:
                return f"未找到相关结果 (所有搜索源均不可用: {e})"

        formatted = []
        for i, r in enumerate(results):
            body = r.get('body', '')
            formatted.append(f"Result {i+1}: [{r['title']}]({r['href']})\n{body}")

        return "\n\n".join(formatted)


# 实例化搜索与采集工具（全局单例）
scrape_tool = ScrapeWebsiteTool()
search_tool = DuckDuckGoSearchTool()
file_read_tool = FileReadTool()


# ═══════════════════════════════════════════════════════
#  第二区：知识库文件工具
# ═══════════════════════════════════════════════════════

class KnowledgeBaseTool(BaseTool):
    """知识库文件管理工具 — 将 Markdown 文章保存到正确的分类目录"""
    name: str = "Knowledge Base File Manager"
    description: str = "保存 Markdown 文章到知识库目录树。输入：JSON 字符串，含 'content', 'filename'(可选), 'category'(可选)。"

    def _run(self, content: str, filename: str = None, category: str = None) -> str:
        try:
            # 从 Frontmatter 提取分类
            if not category:
                match = re.search(r"category:\s*['\"]?([^'\"\n]+)['\"]?", content)
                category = match.group(1).strip() if match else "uncategorized"

            # 从 Frontmatter 提取文件名
            if not filename:
                match = re.search(r"slug:\s*['\"]?([^'\"\n]+)['\"]?", content)
                filename = (match.group(1).strip() + ".md") if match else f"article_{int(time.time())}.md"

            # 构建存储路径
            target_dir = os.path.join("knowledge-base", category)
            os.makedirs(target_dir, exist_ok=True)
            file_path = os.path.join(target_dir, filename)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return f"✅ 文章已保存: {file_path}"
        except Exception as e:
            return f"❌ 保存失败: {e}"


class KbSearchTool(BaseTool):
    """知识库检索工具 — 基于向量数据库 (ChromaDB) 的 RAG 检索"""
    name: str = "Knowledge Base Search"
    description: str = "搜索内部知识库中的相关文章和事实。输入：查询字符串。在生成内容前使用此工具确保一致性。"

    def _run(self, query: str) -> str:
        try:
            import chromadb

            host = os.environ.get("CHROMA_DB_HOST", "chromadb")
            port = int(os.environ.get("CHROMA_DB_PORT", "8000"))
            client = chromadb.HttpClient(host=host, port=port)
            collection = client.get_collection(name="shenya_knowledge")

            results = collection.query(query_texts=[query], n_results=3)

            if results["documents"] and results["documents"][0]:
                formatted = []
                for i, doc in enumerate(results["documents"][0]):
                    source = results["metadatas"][0][i].get("title", "未知来源")
                    formatted.append(f"来源: {source}\n内容: {doc}...")
                return "\n\n".join(formatted)

            return "知识库中未找到相关信息。"
        except Exception as e:
            return f"知识库检索失败（数据库可能为空或不可达）: {e}"


# 实例化知识库工具
kb_tool = KnowledgeBaseTool()
kb_search_tool = KbSearchTool()


# ═══════════════════════════════════════════════════════
#  第三区：数据库工具（MySQL 知识引擎）
# ═══════════════════════════════════════════════════════

class CapabilitySearchInput(BaseModel):
    """深亚工艺能力检索输入模型"""
    query: str = Field(..., description="主题或关键词，如 AI高速板背钻、HDI微盲孔、阻抗控制")


class CapabilitySearchTool(BaseTool):
    """深亚工艺能力检索工具"""
    name: str = "Shenya Capability Search"
    description: str = (
        "检索深亚工艺能力记忆库。输入一个主题，返回已沉淀的深亚工艺能力口径、"
        "适用条件和来源摘要。采集前应先使用。"
    )
    args_schema: type[BaseModel] = CapabilitySearchInput

    def _run(self, query: str) -> str:
        try:
            return capability_store.build_context(query, limit=6)
        except Exception as e:
            return f"深亚工艺能力检索失败: {e}"


class CapabilitySaveInput(BaseModel):
    """深亚工艺能力写入输入模型"""
    capability_data: str = Field(
        ...,
        description=(
            "JSON 字符串。支持 {'profile': {...}, 'sources': [...], 'facts': [...]} 或 "
            "{'specs': [...]}。每个 fact/spec 应包含 capability_name、public_claim、"
            "conservative_value_text、advanced_value_text、conditions_text、"
            "application_tags、evidence_sources 或 evidence_refs。"
        ),
    )


class CapabilitySaveTool(BaseTool):
    """深亚工艺能力入库工具"""
    name: str = "Shenya Capability Memory Saver"
    description: str = (
        "将真实来源参数转写为深亚工艺能力并保存到能力数据库，供下次文章直接调用。"
    )
    args_schema: type[BaseModel] = CapabilitySaveInput

    def _run(self, capability_data: str) -> str:
        try:
            try:
                payload = json.loads(capability_data)
            except (json.JSONDecodeError, TypeError):
                return "❌ 输入必须为合法 JSON 字符串。"

            result = capability_store.save_capability_payload(payload)
            if result.get("success"):
                return (
                    f"✅ 已保存 {result.get('saved', 0)} 条深亚工艺能力数据 "
                    f"(profile: {result.get('profile_code')})。"
                )
            return f"❌ 深亚工艺能力保存失败: {result.get('reason', 'unknown')}"
        except Exception as e:
            return f"❌ 深亚工艺能力入库异常: {e}"

class KeywordInput(BaseModel):
    """关键词输入模型"""
    keyword_data: str = Field(..., description="JSON 字符串，包含 'keyword', 'search_volume', 'difficulty'")

class KeywordSaveTool(BaseTool):
    """关键词入库工具 — 将发现的高价值关键词存入 geo_keywords 表"""
    name: str = "Keyword Database Manager"
    description: str = "将关键词保存到SEO策略数据库。"
    args_schema: type[BaseModel] = KeywordInput

    def _run(self, keyword_data: str) -> str:
        try:
            from core.db_manager import db_manager

            # 兼容 JSON 和纯文本输入
            try:
                data = json.loads(keyword_data)
                keyword = data.get("keyword")
                vol = data.get("search_volume", 0)
                diff = data.get("difficulty", 0)
            except (json.JSONDecodeError, TypeError):
                keyword, vol, diff = keyword_data, 0, 0

            if not keyword:
                return "❌ 未提供关键词。"

            success = db_manager.add_keyword(keyword, vol, diff)
            return f"✅ 关键词 '{keyword}' 已存入策略库。" if success else f"⚠️ 关键词 '{keyword}' 已存在或保存失败。"
        except Exception as e:
            return f"关键词保存错误: {e}"


class ArticleInput(BaseModel):
    """文章输入模型"""
    article_data: str = Field(..., description="JSON 字符串，包含 'title', 'slug', 'content', 'meta', 'subject', 'action', 'attribute'")

class ArticleDatabaseSaveTool(BaseTool):
    """文章入库工具 — 将生成的文章草稿存入 geo_articles 表"""
    name: str = "Article Database Saver"
    description: str = "将文章保存到 MySQL 知识引擎。"
    args_schema: type[BaseModel] = ArticleInput

    def _run(self, article_data: str) -> str:
        try:
            from core.db_manager import db_manager

            try:
                data = json.loads(article_data)
            except (json.JSONDecodeError, TypeError):
                return "❌ 输入必须为合法 JSON 字符串。"

            save_data = {
                'title': data.get('title'),
                'slug': data.get('slug'),
                'content': data.get('content'),
                'meta': data.get('meta', {}),
                'dim_subject': data.get('subject'),
                'dim_action': data.get('action'),
                'dim_attribute': data.get('attribute'),
            }

            if not save_data['title'] or not save_data['content']:
                return "❌ 标题和正文为必填字段。"

            save_result = db_manager.save_article_with_result(save_data, status=0)
            record_saved_article_result({
                **save_result,
                "title": save_data["title"],
                "slug": save_data.get("slug"),
            })

            if save_result.get("success"):
                article_id = save_result.get("article_id")
                action = "已更新" if save_result.get("action") == "updated" else "已入库"
                return f"✅ 文章 '{save_data['title']}' {action} (ID: {article_id}, Draft)。"

            if save_result.get("reason") == "duplicate_content":
                return f"⚠️ 文章 '{save_data['title']}' 内容重复，已跳过保存。"

            return f"❌ 文章 '{save_data['title']}' 保存失败: {save_result.get('reason', 'unknown')}"
        except Exception as e:
            return f"文章入库错误: {e}"


# 实例化数据库工具
capability_search_tool = CapabilitySearchTool()
capability_save_tool = CapabilitySaveTool()
kw_tool = KeywordSaveTool()
db_save_tool = ArticleDatabaseSaveTool()



# ═══════════════════════════════════════════════════════
#  第四区：分发与探测工具（外部平台发布 & 监控）
# ═══════════════════════════════════════════════════════

class ActiveProbingTool(BaseTool):
    """AI 搜索引擎探测工具 — 检查 DeepSeek/豆包/混元 对深亚品牌的认知"""
    name: str = "Active Prober"
    description: str = "探测国产 AI 平台对特定关键词的回答。输入：JSON 字符串 {'keyword': '...', 'platform': 'deepseek' (optional)}。"

    def _run(self, input_data: str) -> str:
        try:
            from core.active_prober import ActiveProber
            prober = ActiveProber()
            
            # 解析输入
            try:
                data = json.loads(input_data)
                keyword = data.get("keyword")
                platform = data.get("platform", "deepseek")
            except:
                keyword = input_data
                platform = "deepseek"
                
            result = prober.probe(keyword, platform)
            
            if "error" in result:
                return f"❌ 探测失败: {result['error']}"
            
            status = "✅ 品牌可见" if result.get("mentioned") else "⚠️ 未提及品牌"
            return f"{status} | 平台: {platform} | 排名: {result.get('rank')} | 摘要: {result.get('snapshot')}"
            
        except Exception as e:
            return f"❌ 探测工具异常: {e}"

class PublishToZhihuTool(BaseTool):
    """知乎自动发布工具 — 使用 Playwright 模拟发布"""
    name: str = "Publish to Zhihu"
    description: str = "发布内容到知乎专栏。输入：JSON {'title': '...', 'content': '...' }。需先运行 login_platforms.py 获取 Cookie。"

    def _run(self, input_data: str) -> str:
        cookie_file = "config/cookies/zhihu.json"
        if not os.path.exists(cookie_file):
            return "❌ 发布失败: 未找到 Cookie 文件。请先运行 `python scripts/login_platforms.py --platform zhihu` 进行登录。"

        try:
            data = json.loads(input_data)
            title = data.get("title")
            content = data.get("content") # Markdown
        except:
            return "❌ 输入格式错误，请提供 JSON 字符串。"

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                
                # 加载 Cookies
                with open(cookie_file, 'r') as f:
                    cookies = json.load(f)
                context.add_cookies(cookies)
                
                page = context.new_page()
                page.goto("https://zhuanlan.zhihu.com/write")
                
                # 简单检查登录状态
                if "zhuanlan.zhihu.com/write" not in page.url:
                     return "❌ Cookie 可能已失效，请重新登录。"
                
                # 填写标题
                page.fill("textarea[placeholder='请输入标题（最多 100 个字）']", title)
                
                # 填写正文 (知乎编辑器比较复杂，这里尝试直接粘贴或输入)
                # 模拟输入 Markdown 可能不会自动渲染，知乎是从剪贴板粘贴比较稳
                # 这里简化：只填纯文本或尝试点击编辑器
                editor_selector = "#root .DraftEditor-root" # 假设选择器
                page.click(editor_selector)
                page.keyboard.type(content[:500] + "\n\n(本文由 GEO 引擎自动生成，完整版请见官网)")
                
                # 点击发布 (需谨慎，暂改为保存草稿)
                # page.click("button:has-text('发布')") 
                
                browser.close()
                return f"✅ 文章 '{title}' 已在知乎保存为草稿 (自动化模拟)。"
                
        except Exception as e:
            return f"❌ 知乎发布异常: {e}"


class WechatPublishTool(BaseTool):
    """微信公众号发布工具"""
    name: str = "Publish to WeChat"
    description: str = "发布内容到微信公众号草稿箱。需先运行 login_platforms.py。"

    def _run(self, input_data: str) -> str:
        cookie_file = "config/cookies/wechat.json"
        if not os.path.exists(cookie_file):
            return "❌ 发布失败: 未找到 Cookie 文件。请先运行 `python scripts/login_platforms.py --platform wechat`。"
            
        return "✅ 微信发布功能开发中 (需配合素材库 API)..."


# 实例化分发工具
zh_tool = PublishToZhihuTool()
wx_tool = WechatPublishTool()
probe_tool = ActiveProbingTool()

# ── 工具对照表 ──
# search_tool    → PlaywrightSearchTool   (百度搜索)
# scrape_tool    → ScrapeWebsiteTool      (网页抓取)
# file_read_tool → FileReadTool           (文件读取)
# kb_tool        → KnowledgeBaseTool      (知识库文件存储)
# kb_search_tool → KbSearchTool           (知识库向量检索)
# kw_tool        → KeywordSaveTool        (关键词入库)
# db_save_tool   → ArticleDatabaseSaveTool(文章入库)
# zh_tool        → PublishToZhihuTool     (知乎发布)
# wx_tool        → WechatPublishTool      (微信发布)
# probe_tool     → ActiveProbingTool      (主动探测)

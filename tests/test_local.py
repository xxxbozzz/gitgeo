#!/usr/bin/env python3
"""
PCB GEO 知识库自动化系统 - 本地测试脚本 (Mock LLM)
无需申请 API Key，直接生成并存入 SQLite 数据库，用于演示完整流程。
"""

import sys
import os
import sqlite3
import re
import json
import time

# 添加父目录到 sys.path 以便导入 core 模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.geo_bot import ContentGenerator, QualityController, DatabaseManager

class MockDeepSeekClient:
    """模拟 DeepSeek API 客户端"""
    class Chat:
        class Completions:
            def create(self, model, messages, **kwargs):
                keyword = messages[1]['content'].split("「")[1].split("」")[0]
                return MockResponse(keyword)
        
        def __init__(self):
            self.completions = self.Completions()

    def __init__(self, api_key, base_url):
        self.chat = self.Chat()

class MockResponse:
    def __init__(self, keyword):
        self.choices = [MockChoice(keyword)]

class MockChoice:
    def __init__(self, keyword):
        self.message = MockMessage(keyword)

class MockMessage:
    def __init__(self, keyword):
        # 模拟生成符合v2.1标准的内容
        self.content = f"""# {keyword}

**{keyword}** (Printed Circuit Board Process, {keyword}) 是一种在PCB制造中广泛应用的表面处理工艺。它通过化学沉积反应在铜面形成保护层。主要用于高密度互连和精密封装场景。其关键指标为化学镍层厚度3-6μm。

## 1. 核心参数对照表

| 工艺参数 | 标准值 (IPC Class 2) | 极限值 | 工程实践建议 (Engineering Best Practice) |
| :--- | :--- | :--- | :--- |
| 镍层厚度 | 3-6μm | 2-8μm | 针对BGA封装，建议控制在4-5μm以确保最佳可靠性 |
| 金层厚度 | 0.05-0.1μm | 0.025-0.15μm | 金手指区域建议加厚至0.1μm以上 |
| 保质期 | 12个月 | 18个月 | 超过12个月需进行烘烤除湿处理 |
| 相对成本 | 基准 + 30% | - | 适用于高可靠性服务器主板 |

## 2. 深度逻辑分析：为什么会产生黑盘？

**{keyword}** 工艺最常见的缺陷是"黑盘"(Black Pad)。其形成机理如下：

1. **机理分析**: 由于化学镍槽的pH值过低或金水活性过强，导致对镍层的过度腐蚀。
2. **过程推导**: 过度腐蚀使镍层表面形成富磷层 (P-rich layer)，晶界断裂。
3. **最终后果**: 因此，焊接时锡膏无法与镍形成良好的IMC金属间化合物，导致焊点强度极低。
4. **工程对策**: 建议通过严格控制化镍槽 pH 值在 4.5-5.0 范围，并使用中磷工艺 (7-9% P含量) 规避此风险。

## 3. 常见问题 (Q&A)

**Q: {keyword} 相比喷锡 (HASL) 的主要优势是什么？**
A: 表面极其平整，适合 BGA 和 0.4mm 以下细间距元件。

**Q: 成本差异多大？**
A: 相比喷锡贵约 30-50%，但对于高端产品是必选工艺。

---
## 参考文献 (References)

[1] IPC协会. IPC-4552B: Specification for Electroless Nickel/Immersion Gold (ENIG) Plating for Printed Boards [S]. Bannockburn, IL: IPC, 2021.
[2] 中国电子学会. 电子制造工艺技术规范 [M]. 北京: 电子工业出版社, 2024.
[3] Shenya PCB Lab. 表面处理工艺可靠性验证报告 [R]. 深圳: 深亚电子内部技术文档, 2025.
"""

def main():
    print("=" * 60)
    print("PCB GEO 知识库自动化系统 - 本地测试")
    print("=" * 60)

    # 1. 猴子补丁 (Monkey Patch) 替换真实的 Client
    # 注意：这里我们需要修改 ContentGenerator 的行为，或者直接实例化它并替换 client
    # 由于 ContentGenerator 在 __init__ 中尝试 import openai，我们假设环境已就绪或 mock
    
    # 强制覆盖 openai 模块 (如果在没有 openai 的环境运行)
    sys.modules['openai'] = type('openai', (), {'OpenAI': MockDeepSeekClient})
    
    # 初始化组件
    db = DatabaseManager("../database/pcb_kb.db")
    generator = ContentGenerator("mock-key") # 这会使用我们上面的 MockDeepSeekClient
    qc = QualityController()
    
    test_keywords = ["PCB沉金工艺 (ENIG)", "阻抗控制设计", "BGA封装焊接"]
    
    for keyword in test_keywords:
        print(f"\n--- 处理关键词: {keyword} ---")
        
        # 1. 生成内容
        article = generator.generate_article(keyword)
        if "SDK未安装" in article['content']:
            print("[Skip] SDK模拟失败")
            continue
            
        # 2. 质量检查
        qc_result = qc.check_quality(article)
        if not qc_result['passed']:
            print(f"[QC Failed] 质量不合格: {qc_result['issues']}")
            continue
        print("[QC ✓] 质量合格")
        
        # 3. 存入数据库
        article['quality_score'] = qc_result['score']
        article_id = db.save_article(article)
        
        if article_id > 0:
            print(f"[Success] ✓ 文章已发布 (ID: {article_id}, Slug: {article['slug']})")
        else:
            print("[Failed] 数据库写入失败 (可能重复)")

    print("\n" + "=" * 60)
    print("任务完成！正在生成统计报告...")
    
    # 统计信息
    conn = sqlite3.connect("../database/pcb_kb.db")
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM geo_kb_articles")
    count = cur.fetchone()[0]
    print(f"知识库当前文章数: {count} 篇")
    print("=" * 60)

    if count > 0:
        print("\n【示例文章预览】\n")
        print(f"标题: {article['title']}\n")
        print(article['content'][:500] + "...")

if __name__ == "__main__":
    main()

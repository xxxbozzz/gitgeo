"""
知识库目录初始化脚本 (Knowledge Base Initializer)
==================================================
生成标准的知识库目录树和 v2.1 文章模板。

目录结构遵循多维标签树设计：
    knowledge-base/
    ├── process/       → 工艺类 (surface_finish, lamination, drilling, etching)
    ├── material/      → 材料类 (copper_foil, substrate, solder_mask)
    ├── application/   → 应用类 (automotive, communication, consumer)
    ├── design/        → 设计类
    ├── reliability/   → 可靠性类
    ├── industry/      → 行业类
    └── assets/        → 素材目录 (images)

使用方法：
    python scripts/init_knowledge_base.py
"""

import os
import datetime

ROOT_DIR = "knowledge-base"

# 分类树定义：一级分类 → 二级分类列表
STRUCTURE = {
    "process": ["surface_finish", "lamination", "drilling", "etching"],
    "material": ["copper_foil", "substrate", "solder_mask"],
    "application": ["automotive", "communication", "consumer"],
    "design": [],
    "reliability": [],
    "industry": [],
    "assets": ["images"],
}

# 分类缩写映射（用于生成文章 ID）
CATEGORY_ABBR = {
    "process": "proc",
    "material": "mat",
    "application": "app",
    "design": "des",
    "reliability": "rel",
    "industry": "ind",
}

# v2.1 标准文章模板
TEMPLATE = """---
title: "{title}"
id: "{article_id}"
version: "2.1"
created: "{date}"
updated: "{date}"
author: "深亚技术团队"
category: "{category}"
tags: []
references:
  - "IPC-Std-XXXX"
abstract: "在这里填写文章摘要..."
---

## 1. 核心定义
**[核心概念]** ([English Name]) 是一种...

## 2. 核心参数与工程建议
| 参数指标 | IPC 标准值 | 工程实践建议 |
|---------|------------|-------------|
| 参数A    | 范围X      | 建议Y       |

## 3. 深度逻辑分析（Chain of Thought）
**为什么会发生...？**
由于...导致...因此...

## 4. 常见问题（FAQ）
**Q: ...?**
A: ...

## 5. 参考文献
[1] IPC Association...
"""


def create_structure():
    """生成知识库目录树和模板文件"""
    os.makedirs(ROOT_DIR, exist_ok=True)
    print(f"📂 知识库根目录: {ROOT_DIR}")

    today = datetime.date.today().isoformat()

    for category, subcategories in STRUCTURE.items():
        category_path = os.path.join(ROOT_DIR, category)
        os.makedirs(category_path, exist_ok=True)
        print(f"  ├── {category}/")

        # 为非素材目录创建模板
        if category != "assets":
            _write_template(category_path, category, today)

        for sub in subcategories:
            sub_path = os.path.join(category_path, sub)
            os.makedirs(sub_path, exist_ok=True)
            print(f"  │   ├── {sub}/")

            if category != "assets":
                _write_template(sub_path, f"{category}/{sub}", today, sub)


def _write_template(path: str, category: str, date: str, sub: str = None):
    """写入模板文件到指定目录"""
    abbr = CATEGORY_ABBR.get(category.split('/')[0], "gen")
    if sub:
        article_id = f"{abbr}-{sub[:3]}-001"
        title = f"[Template] {sub} Article"
    else:
        article_id = f"{abbr}-001"
        title = f"[Template] {category} Article"

    template_path = os.path.join(path, "_template.md")
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(
            title=title,
            article_id=article_id,
            date=date,
            category=category,
        ))


if __name__ == "__main__":
    create_structure()
    print("\n✅ 知识库目录结构初始化完成！")

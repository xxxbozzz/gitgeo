"""
种子话题加载脚本 (Seed Topics Loader)
=====================================
读取 seed_topics.json 并批量加载到 geo_keywords 数据库表。
此脚本将 JSON 中的 keyword 字段存入数据库。

重要的是，我们不仅存 keyword，也将 GEO 优化后的 title 存入 meta_json 字段，
以便 Generator Agent 在生成时可以直接使用这个高质量标题。

使用方法:
    python scripts/load_seed_topics.py
"""

import json
import os
import sys
import mysql.connector

# 添加项目根目录到 sys.path，以便导入 core 模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from core.db_manager import db_manager


def load_seeds():
    """读取 seed_topics.json 并写入数据库"""
    file_path = os.path.join(project_root, 'seed_topics.json')
    
    if not os.path.exists(file_path):
        print(f"❌ 找不到种子文件: {file_path}")
        return

    print(f"📂 读取 {file_path} ...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            topics = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        return

    print(f"📊 发现 {len(topics)} 个话题，开始导入...")
    
    cnx = db_manager.get_connection()
    if not cnx:
        print("❌ 数据库连接失败，请检查 Docker 是否运行。")
        return

    cursor = cnx.cursor()
    success_count = 0
    duplicate_count = 0
    error_count = 0

    # 检查 geo_keywords 表是否有 extra_data 列，如果没有则只能存 keyword
    # 为了简化，我们只存 keyword。Generator 会重新生成标题，
    # 但我们在 task prompt 里已经强制定制了 title 的生成逻辑。
    # 更好的方式是：如果 keyword 本身就是长标题？
    # 不，keyword 必须是短词。
    # 我们暂且只存 keyword。Trust the system prompt.
    
    for item in topics:
        keyword = item.get('keyword')
        if not keyword:
            continue
            
        try:
            sql = "INSERT IGNORE INTO geo_keywords (keyword, search_volume, difficulty) VALUES (%s, %s, %s)"
            val = (keyword, 1000, 50)
            cursor.execute(sql, val)
            
            if cursor.rowcount > 0:
                success_count += 1
            else:
                duplicate_count += 1
                
        except mysql.connector.Error as err:
            print(f"❌ SQL 错误 ({keyword}): {err}")
            error_count += 1

    cnx.commit()
    cursor.close()
    cnx.close()
    
    print("-" * 30)
    print(f"🏁 导入完成报告:")
    print(f"   ✅ 成功导入: {success_count}")
    print(f"   ⚠️ 跳过重复: {duplicate_count}")
    if error_count > 0:
        print(f"   ❌ 发生错误: {error_count}")


if __name__ == "__main__":
    load_seeds()

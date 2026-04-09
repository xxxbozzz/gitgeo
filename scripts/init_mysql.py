"""
MySQL 数据库初始化脚本 (Database Initialization)
==================================================
在 Docker 容器启动后运行，负责：
    1. 等待 MySQL 就绪
    2. 创建 geo_knowledge_engine 数据库
    3. 执行 database/schema.sql 创建表结构

使用方法：
    docker compose exec -T geo-agent-app python scripts/init_mysql.py
"""

import os
import time

import mysql.connector
from mysql.connector import errorcode

# ─── 配置（不含数据库名，因为要先创建它） ───
DB_CONFIG = {
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'root_password'),
    'host': os.environ.get('DB_HOST', 'mysql_db'),
    'port': 3306,
    'raise_on_warnings': False,
}

DB_NAME = 'geo_knowledge_engine'
SCHEMA_FILE = 'database/schema.sql'


def wait_for_db(max_retries: int = 30, interval: int = 2) -> bool:
    """等待 MySQL 服务就绪"""
    print("⏳ 等待 MySQL 就绪...")
    for i in range(max_retries):
        try:
            cnx = mysql.connector.connect(**DB_CONFIG)
            cnx.close()
            print("✅ MySQL 已就绪！")
            return True
        except mysql.connector.Error as err:
            print(f"  MySQL 未就绪 ({err})，{interval}s 后重试... ({i+1}/{max_retries})")
            time.sleep(interval)
    return False


def init_db():
    """创建数据库并执行 Schema 文件"""
    if not wait_for_db():
        print("❌ 无法连接 MySQL，初始化中止。")
        exit(1)

    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()

        # 创建数据库
        try:
            cursor.execute(f"CREATE DATABASE {DB_NAME} DEFAULT CHARACTER SET 'utf8mb4'")
            print(f"📂 数据库 {DB_NAME} 创建成功")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_DB_CREATE_EXISTS:
                print(f"ℹ️  数据库 {DB_NAME} 已存在")
            else:
                print(f"❌ 创建数据库失败: {err}")
                exit(1)

        cnx.database = DB_NAME

        # 执行 Schema
        print(f"📜 执行 Schema: {SCHEMA_FILE}")
        with open(SCHEMA_FILE, 'r') as f:
            schema_sql = f.read()

        for command in schema_sql.split(';'):
            command = command.strip()
            if command:
                try:
                    cursor.execute(command)
                except mysql.connector.Error as err:
                    print(f"  ⚠️ SQL 执行异常: {command[:50]}... → {err}")

        print("✅ Schema 执行完成！")
        cursor.close()
        cnx.close()

    except mysql.connector.Error as err:
        print(f"❌ 数据库连接失败: {err}")
        exit(1)


if __name__ == "__main__":
    init_db()

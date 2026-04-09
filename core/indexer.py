"""
知识库向量索引器 (Knowledge Base Indexer)
==========================================
本模块负责将 knowledge-base/ 目录下的 Markdown 文章
分块后存入 ChromaDB 向量数据库，供 RAG 检索使用。

工作流程：
    1. 连接 ChromaDB 服务器
    2. 遍历 knowledge-base/ 下的 .md 文件
    3. 使用 python-frontmatter 解析元数据
    4. 按固定窗口分块（800字符，100字符重叠）
    5. 批量 upsert 到向量数据库

使用方法：
    python core/indexer.py
"""

import os
import chromadb
from chromadb.utils import embedding_functions
import frontmatter

# ─── 配置 ───
CHROMA_HOST = os.environ.get("CHROMA_DB_HOST", "localhost")
CHROMA_PORT = os.environ.get("CHROMA_DB_PORT", "8000")
COLLECTION_NAME = "shenya_knowledge"
KB_ROOT = "knowledge-base"


def get_chroma_client():
    """连接 ChromaDB 服务器"""
    try:
        return chromadb.HttpClient(host=CHROMA_HOST, port=int(CHROMA_PORT))
    except Exception as e:
        print(f"❌ 连接 ChromaDB 失败 ({CHROMA_HOST}:{CHROMA_PORT}): {e}")
        return None


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list:
    """
    将长文本按固定窗口分块

    参数:
        text: 原始文本
        chunk_size: 每块大小（字符数）
        overlap: 相邻块的重叠字符数
    """
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size - overlap
    return chunks


def index_knowledge_base():
    """扫描知识库目录，将所有文章分块后存入向量数据库"""
    client = get_chroma_client()
    if not client:
        return

    # 使用本地轻量级嵌入模型
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    try:
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=emb_fn,
            metadata={"hnsw:space": "cosine"},
        )
    except Exception as e:
        print(f"❌ 创建集合失败: {e}")
        return

    print(f"📂 扫描 {KB_ROOT}/ 目录进行索引...")
    count = 0

    for root, dirs, files in os.walk(KB_ROOT):
        for file in files:
            # 跳过模板文件和非 Markdown 文件
            if not file.endswith(".md") or file.startswith("_"):
                continue

            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    post = frontmatter.load(f)

                metadata = post.metadata
                article_id = metadata.get("id", file)
                title = metadata.get("title", file)
                category = metadata.get("category", "unknown")

                chunks = chunk_text(post.content)

                ids = []
                documents = []
                metadatas = []

                for i, chunk in enumerate(chunks):
                    ids.append(f"{article_id}_chunk_{i}")
                    documents.append(chunk)
                    chunk_meta = {
                        "article_id": str(article_id),
                        "title": str(title),
                        "category": str(category),
                        "chunk_index": i,
                        "source": file_path,
                    }
                    # 标签列表转为逗号分隔字符串（ChromaDB 不支持嵌套数据）
                    if "tags" in metadata and isinstance(metadata["tags"], list):
                        chunk_meta["tags"] = ",".join(metadata["tags"])
                    metadatas.append(chunk_meta)

                if ids:
                    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
                    count += 1
                    print(f"  ✅ 已索引: {file} ({len(ids)} 块)")

            except Exception as e:
                print(f"  ⚠️ 跳过 {file}: {e}")

    print(f"\n🎉 索引完成！共处理 {count} 篇文章。")


if __name__ == "__main__":
    index_knowledge_base()

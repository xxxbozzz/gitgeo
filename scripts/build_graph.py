
import os
import re
import mysql.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root_password"),
        database=os.getenv("DB_NAME", "geo_knowledge_engine")
    )

def build_graph():
    print("🚀 Starting Knowledge Graph Builder...")
    try:
        cnx = get_connection()
        cursor = cnx.cursor(dictionary=True)
        
        # 1. Fetch all articles
        print("📥 Fetching articles...")
        cursor.execute("SELECT id, title, content_markdown FROM geo_articles")
        articles = cursor.fetchall()
        print(f"   Found {len(articles)} articles.")
        
        if not articles:
            print("❌ No articles found. Cannot build graph.")
            return

        # 2. Build Title Map (Title -> ID)
        # Filter out short titles to avoid noise
        title_map = {a['title']: a['id'] for a in articles if len(a['title']) > 2}
        
        links = []
        existing_pairs = set()

        print("🔍 Scanning content for internal links...")
        for src in articles:
            content = src['content_markdown']
            if not content: continue
            
            # Check for mentions of other titles
            for tgt_title, tgt_id in title_map.items():
                if src['id'] == tgt_id: continue
                
                # Check if target title exists in source content
                # Use simple string search first for speed, then regex word boundary if needed
                if tgt_title in content:
                    pair = (src['id'], tgt_id)
                    if pair not in existing_pairs:
                        links.append((src['id'], tgt_id, tgt_title))
                        existing_pairs.add(pair)
        
        print(f"   Identified {len(links)} potential links.")

        # 3. Update Database
        if links:
            print("💾 Saving to database...")
            cursor.execute("TRUNCATE TABLE geo_links")
            cursor.executemany(
                "INSERT INTO geo_links (source_id, target_id, anchor_text) VALUES (%s, %s, %s)",
                links
            )
            cnx.commit()
            print(f"✅ Successfully created {len(links)} internal links.")
        else:
            print("⚠️ No links generated.")

        cursor.close()
        cnx.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    build_graph()

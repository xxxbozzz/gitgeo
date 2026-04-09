"""
Reset Articles Script
=====================
This script clears all generated articles and resets keyword status.
Run this to restart production from scratch.
"""
import sys
import os

# Add parent dir to path to allow importing 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db_manager import db_manager

def reset_articles():
    print("🗑️ Cleansing database of generated content...")
    cnx = db_manager.get_connection()
    if not cnx:
        print("❌ Database connection failed.")
        return

    cursor = cnx.cursor()
    try:
        # 1. Reset keywords
        cursor.execute("UPDATE geo_keywords SET target_article_id = NULL")
        print("✅ Keywords reset to pending.")
        
        # 2. Clear links
        cursor.execute("TRUNCATE TABLE geo_links")
        print("✅ Knowledge graph links cleared.")
        
        # 3. Clear articles
        # MySQL doesn't support TRUNCATE with foreign keys sometimes, but geo_articles is parent.
        # But if geo_links refers to it? geo_links has FK?
        # Schema doesn't define FK constraints explicitly (no FOREIGN KEY ...).
        # So TRUNCATE is safe.
        cursor.execute("TRUNCATE TABLE geo_articles")
        print("✅ Articles cleared.")
        
        cnx.commit()
        print("🚀 Ready for fresh generation!")
        
    except Exception as e:
        print(f"❌ Reset failed: {e}")
        cnx.rollback()
    finally:
        cursor.close()
        cnx.close()

if __name__ == "__main__":
    reset_articles()

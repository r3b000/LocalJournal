"""
Database Migration: Add screenshot_category column
Run this once to update your database schema
"""

from pathlib import Path
import sqlite3
import logging
from database.connection import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_screenshots_table(db_path: Path) -> bool:
    """
    Add screenshot_category column to screenshots table
    
    Returns:
        bool: True if successful or already exists
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if column exists
            cursor.execute("PRAGMA table_info(screenshots)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'screenshot_category' in columns:
                logger.info("✔ screenshot_category column already exists")
                return True
            
            # Add column
            logger.info("🔧 Adding screenshot_category column...")
            
            cursor.execute("""
                ALTER TABLE screenshots
                ADD COLUMN screenshot_category TEXT
            """)
            
            logger.info("✔ Migration successful! screenshot_category column added")
            return True
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False


def verify_migration(db_path: Path):
    """Verify the migration was successful"""
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Get table schema
            cursor.execute("PRAGMA table_info(screenshots)")
            columns = cursor.fetchall()
            
            print("\n𝄜 Current screenshots table schema:")
            print("-" * 50)
            for col in columns:
                col_id, name, col_type, notnull, default, pk = col
                print(f"  {name:25} {col_type:15} {'PK' if pk else ''}")
            print("-" * 50)
            
            # Check for screenshot_category
            column_names = [col[1] for col in columns]
            
            if 'screenshot_category' in column_names:
                print("✔ Migration verified: screenshot_category column exists\n")
                return True
            else:
                print("❌ Migration verification failed: screenshot_category column missing\n")
                return False
                
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    from utils.paths import get_database_path
    
    print("=" * 50)
    print("🔧 Database Migration: Screenshots Table")
    print("=" * 50)
    
    db_path = get_database_path()
    
    print(f"\n📁 Database: {db_path}")
    print(f"𝄜 Database exists: {db_path.exists()}")
    
    if not db_path.exists():
        print("\n❌ Database not found! Please create your database first.")
        exit(1)
    
    # Run migration
    print("\n🚀 Starting migration...")
    success = migrate_screenshots_table(db_path)
    
    if success:
        print("\n✔ Migration completed successfully!")
        
        # Verify
        print("\n⌕ Verifying migration...")
        verify_migration(db_path)
    else:
        print("\n❌ Migration failed!")
        exit(1)

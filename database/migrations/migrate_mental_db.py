"""
Migration script to update mental development database schema
Run this once to migrate from old to new dual-tracker system
"""

import sqlite3
import logging
from pathlib import Path
from utils.paths import get_database_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_mental_database():
    """Migrate database to new dual-tracker schema"""
    
    db_path = get_database_path()
    
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        logger.info("Starting mental development database migration...")
        
        # Check if old issue_trackers table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='issue_trackers'
        """)
        old_table_exists = cursor.fetchone() is not None
        
        # Check if emotion_trackers already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='emotion_trackers'
        """)
        emotion_table_exists = cursor.fetchone() is not None
        
        if emotion_table_exists:
            logger.info("emotion_trackers table already exists. Skipping creation.")
        else:
            logger.info("Creating emotion_trackers table...")
            cursor.execute("""
                CREATE TABLE emotion_trackers (
                    emotion_tracker_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    issue_category TEXT NOT NULL CHECK(issue_category IN (
                        'Trade Execution',
                        'Risk Management',
                        'Trade Management'
                    )),
                    emotion TEXT NOT NULL,
                    occurrence_count INTEGER DEFAULT 0,
                    last_occurred TIMESTAMP,
                    worksheet_completed BOOLEAN DEFAULT 0,
                    last_reset TIMESTAMP,
                    
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE,
                    UNIQUE(account_id, issue_category, emotion)
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_emotion_trackers_account ON emotion_trackers(account_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_emotion_trackers_category ON emotion_trackers(issue_category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_emotion_trackers_emotion ON emotion_trackers(emotion)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_emotion_trackers_count ON emotion_trackers(occurrence_count)")
            logger.info("emotion_trackers table created successfully")
        
        if old_table_exists:
            # Check if old table has 'emotion' column (old schema)
            cursor.execute("PRAGMA table_info(issue_trackers)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'emotion' in columns:
                logger.info("Old schema detected. Migrating to dual-tracker system...")
                
                # Rename old table
                cursor.execute("ALTER TABLE issue_trackers RENAME TO issue_trackers_old")
                
                # Create new issue_trackers table (without emotion column)
                logger.info("Creating new issue_trackers table...")
                cursor.execute("""
                    CREATE TABLE issue_trackers (
                        issue_tracker_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_id INTEGER NOT NULL,
                        issue_category TEXT NOT NULL CHECK(issue_category IN (
                            'Trade Execution',
                            'Risk Management',
                            'Trade Management'
                        )),
                        issue_type TEXT NOT NULL,
                        occurrence_count INTEGER DEFAULT 0,
                        last_occurred TIMESTAMP,
                        worksheet_completed BOOLEAN DEFAULT 0,
                        last_reset TIMESTAMP,
                        
                        FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE,
                        UNIQUE(account_id, issue_category, issue_type)
                    )
                """)
                
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_issue_trackers_account ON issue_trackers(account_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_issue_trackers_category ON issue_trackers(issue_category)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_issue_trackers_type ON issue_trackers(issue_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_issue_trackers_count ON issue_trackers(occurrence_count)")
                
                # Migrate data to emotion_trackers
                if not emotion_table_exists:
                    logger.info("Migrating emotion data...")
                    cursor.execute("""
                        INSERT OR IGNORE INTO emotion_trackers (
                            account_id, issue_category, emotion, occurrence_count, 
                            last_occurred, worksheet_completed
                        )
                        SELECT 
                            account_id, issue_category, emotion,
                            SUM(occurrence_count) as occurrence_count,
                            MAX(last_occurred) as last_occurred,
                            MAX(worksheet_completed) as worksheet_completed
                        FROM issue_trackers_old
                        GROUP BY account_id, issue_category, emotion
                    """)
                
                # Migrate data to new issue_trackers
                logger.info("Migrating issue data...")
                cursor.execute("""
                    INSERT OR IGNORE INTO issue_trackers (
                        account_id, issue_category, issue_type, occurrence_count,
                        last_occurred, worksheet_completed
                    )
                    SELECT 
                        account_id, issue_category, issue_type,
                        SUM(occurrence_count) as occurrence_count,
                        MAX(last_occurred) as last_occurred,
                        MAX(worksheet_completed) as worksheet_completed
                    FROM issue_trackers_old
                    GROUP BY account_id, issue_category, issue_type
                """)
                
                # Drop old table
                cursor.execute("DROP TABLE issue_trackers_old")
                logger.info("Old table dropped")
            else:
                logger.info("issue_trackers table already migrated")
        else:
            # Create fresh issue_trackers table
            logger.info("Creating fresh issue_trackers table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS issue_trackers (
                    issue_tracker_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    issue_category TEXT NOT NULL CHECK(issue_category IN (
                        'Trade Execution',
                        'Risk Management',
                        'Trade Management'
                    )),
                    issue_type TEXT NOT NULL,
                    occurrence_count INTEGER DEFAULT 0,
                    last_occurred TIMESTAMP,
                    worksheet_completed BOOLEAN DEFAULT 0,
                    last_reset TIMESTAMP,
                    
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE,
                    UNIQUE(account_id, issue_category, issue_type)
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_issue_trackers_account ON issue_trackers(account_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_issue_trackers_category ON issue_trackers(issue_category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_issue_trackers_type ON issue_trackers(issue_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_issue_trackers_count ON issue_trackers(occurrence_count)")
        
        # Update mental_worksheets table
        cursor.execute("PRAGMA table_info(mental_worksheets)")
        ws_columns = [col[1] for col in cursor.fetchall()]
        
        if 'trigger_type' not in ws_columns:
            logger.info("Updating mental_worksheets table...")
            
            # Rename old table
            cursor.execute("ALTER TABLE mental_worksheets RENAME TO mental_worksheets_old")
            
            # Create new table
            cursor.execute("""
                CREATE TABLE mental_worksheets (
                    worksheet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    issue_category TEXT NOT NULL CHECK(issue_category IN (
                        'Trade Execution',
                        'Risk Management',
                        'Trade Management'
                    )),
                    trigger_type TEXT NOT NULL CHECK(trigger_type IN ('EMOTION', 'ISSUE')),
                    trigger_value TEXT NOT NULL,
                    occurrence_count INTEGER NOT NULL,
                    
                    emotional_pattern TEXT,
                    root_cause TEXT,
                    challenge_response TEXT,
                    action_plan TEXT,
                    expected_outcome TEXT,
                    
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_worksheets_account ON mental_worksheets(account_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_worksheets_category ON mental_worksheets(issue_category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_worksheets_trigger ON mental_worksheets(trigger_type, trigger_value)")
            
            # Migrate old data (assume all old worksheets were emotion-based)
            cursor.execute("""
                INSERT INTO mental_worksheets (
                    account_id, issue_category, trigger_type, trigger_value, occurrence_count,
                    emotional_pattern, root_cause, challenge_response, action_plan, 
                    expected_outcome, completed_at
                )
                SELECT 
                    account_id, issue_category, 'EMOTION', emotion, occurrence_count,
                    emotional_pattern, root_cause, challenge_response, action_plan,
                    expected_outcome, completed_at
                FROM mental_worksheets_old
            """)
            
            # Drop old table
            cursor.execute("DROP TABLE mental_worksheets_old")
            logger.info("mental_worksheets table updated successfully")
        else:
            logger.info("mental_worksheets table already updated")
        
        conn.commit()
        conn.close()
        
        logger.info("✔ Database migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("MENTAL DEVELOPMENT DATABASE MIGRATION")
    print("=" * 60)
    print("\nThis will update your database schema to support dual tracking.")
    print("Your existing data will be preserved.\n")
    
    response = input("Continue with migration? (yes/no): ").strip().lower()
    
    if response == 'yes':
        success = migrate_mental_database()
        if success:
            print("\n✔ Migration completed! You can now use the Mental Development page.")
        else:
            print("\n❌ Migration failed. Check the logs above for details.")
    else:
        print("\nMigration cancelled.")

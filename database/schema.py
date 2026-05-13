"""
Database schema management
Handles table creation and migrations
"""

import sqlite3
from pathlib import Path
import logging


logger = logging.getLogger(__name__)


def initialize_database(db_path: Path) -> bool:
    """
    Initialize database with all required tables
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create all tables
        _create_accounts_table(cursor)
        _create_strategies_table(cursor)
        _create_trades_table(cursor)
        _create_screenshots_table(cursor)
        _create_mental_issues_table(cursor)
        _create_mental_worksheets_table(cursor)
        _create_emotion_trackers_table(cursor)  # NEW
        _create_issue_trackers_table(cursor)     # UPDATED
        _create_app_metadata_table(cursor)
        
        # Composite indexes for faster filtered queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_account_status_date 
                ON trades(account_id, status, entry_date DESC, entry_time DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_account_pnl 
                ON trades(account_id, pnl) WHERE status = 'CLOSED'
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_exit_date 
                ON trades(exit_date DESC, exit_time DESC) WHERE status = 'CLOSED'
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mental_account_category
                ON mental_issues(account_id, issue_category, logged_at DESC)
        """)
        
        logger.info("Composite indexes created successfully")
        
        conn.commit()
        conn.close()
        
        logger.info("Database schema initialized successfully")
        return True

        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def _create_accounts_table(cursor):
    """Create accounts table"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT UNIQUE NOT NULL,
            starting_equity REAL NOT NULL,
            current_equity REAL NOT NULL,
            strategy_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_name ON accounts(account_name)")
    logger.debug("Accounts table created")


def _create_strategies_table(cursor):
    """Create strategies table"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_strategies_name ON strategies(strategy_name)")
    logger.debug("Strategies table created")


def _create_trades_table(cursor):
    """Create trades table"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            
            symbol TEXT NOT NULL,
            direction TEXT NOT NULL CHECK(direction IN ('LONG', 'SHORT')),
            strategy_id INTEGER,
            
            entry_date DATE NOT NULL,
            entry_time TEXT NOT NULL,
            entry_price REAL NOT NULL,
            
            trading_environment TEXT,
            trigger TEXT,
            
            multi_entry_price REAL,
            stop_loss REAL NOT NULL,
            target REAL,
            risk_amount REAL NOT NULL,
            risk_percentage REAL NOT NULL,
            position_size REAL NOT NULL,
            fta REAL,
            prospective_r REAL,
            within_risk_limit BOOLEAN DEFAULT 1,
            
            exit_date DATE,
            exit_time TEXT,
            multi_exit_price REAL,
            target_hit BOOLEAN,
            stop_loss_hit BOOLEAN,
            
            mae REAL,
            mfe REAL,
            trade_duration INTEGER,
            total_r REAL,
            roe_percentage REAL,
            pnl REAL DEFAULT 0,
            
            grade_mentally TEXT CHECK(grade_mentally IN ('A', 'B', 'C', 'D', 'F', NULL)),
            grade_technically TEXT CHECK(grade_technically IN ('A', 'B', 'C', 'D', 'F', NULL)),
            
            setup_idea TEXT,
            trade_notes_entry TEXT,
            trade_notes_management TEXT,
            trade_notes_closing TEXT,
            reason_for_closing TEXT,
            final_notes TEXT,
            
            commission REAL DEFAULT 0,

            status TEXT NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN', 'CLOSED')),
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE,
            FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id) ON DELETE SET NULL
        )
    """)
    
    # Create indexes
    indexes = [
        # Existing indexes
        "CREATE INDEX IF NOT EXISTS idx_trades_account ON trades(account_id)",
        "CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)",
        "CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)",
        "CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy_id)",
        "CREATE INDEX IF NOT EXISTS idx_trades_entry_date ON trades(entry_date)",
        "CREATE INDEX IF NOT EXISTS idx_trades_account_status ON trades(account_id, status)",
        
        # NEW: Performance indexes for filtering and sorting
        "CREATE INDEX IF NOT EXISTS idx_trades_direction ON trades(direction)",
        "CREATE INDEX IF NOT EXISTS idx_trades_pnl ON trades(pnl)",
        "CREATE INDEX IF NOT EXISTS idx_trades_grades ON trades(grade_mentally, grade_technically)",
        
        # NEW: Composite indexes for common query patterns
        "CREATE INDEX IF NOT EXISTS idx_trades_account_entry_date ON trades(account_id, entry_date DESC)",
        "CREATE INDEX IF NOT EXISTS idx_trades_account_status_date ON trades(account_id, status, entry_date DESC)",
        "CREATE INDEX IF NOT EXISTS idx_trades_account_symbol ON trades(account_id, symbol)",
        "CREATE INDEX IF NOT EXISTS idx_trades_account_direction ON trades(account_id, direction)",
        "CREATE INDEX IF NOT EXISTS idx_trades_account_status_entry ON trades(account_id, status, entry_date, entry_time)",
        
        # NEW: Covering index for equity curve calculation (most expensive query)
        "CREATE INDEX IF NOT EXISTS idx_trades_equity_curve ON trades(account_id, status, entry_date, entry_time, pnl)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    logger.debug("Trades table created")


def _create_screenshots_table(cursor):
    """Create screenshots table"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screenshots (
            screenshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id INTEGER NOT NULL,
            screenshot_type TEXT CHECK(screenshot_type IN ('ENTRY', 'EXIT', 'OTHER')),
            screenshot_category TEXT,  -- NEW: 'CHART', 'PNL', 'INDICATORS', 'OTHER'
            file_path TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_screenshots_trade ON screenshots(trade_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_screenshots_type ON screenshots(screenshot_type)")
    logger.debug("Screenshots table created")


def _create_mental_issues_table(cursor):
    """Create mental issues table"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mental_issues (
            issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            trade_id INTEGER,
            
            issue_category TEXT NOT NULL CHECK(issue_category IN (
                'Trade Execution',
                'Risk Management',
                'Trade Management'
            )),
            issue_type TEXT NOT NULL,
            emotion TEXT NOT NULL,
            
            comments TEXT,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE,
            FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE SET NULL
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mental_account ON mental_issues(account_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mental_category ON mental_issues(issue_category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mental_type ON mental_issues(issue_type)")
    
    # NEW: Performance indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mental_emotion ON mental_issues(emotion)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mental_logged_at ON mental_issues(logged_at DESC)")

    logger.debug("Mental issues table created")


def _create_mental_worksheets_table(cursor):
    """Create mental worksheets table - UPDATED"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mental_worksheets (
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
    logger.debug("Mental worksheets table created")


def _create_emotion_trackers_table(cursor):
    """Create emotion trackers table - NEW TABLE"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emotion_trackers (
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
    logger.debug("Emotion trackers table created")


def _create_issue_trackers_table(cursor):
    """Create issue trackers table - UPDATED"""
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
    logger.debug("Issue trackers table created")


def _create_app_metadata_table(cursor):
    """Create app metadata table"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_metadata (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert default metadata
    cursor.execute("""
        INSERT OR IGNORE INTO app_metadata (key, value) VALUES 
            ('version', '1.0.0'),
            ('schema_version', '1.0.0'),
            ('first_launch', datetime('now')),
            ('last_backup', NULL)
    """)
    logger.debug("App metadata table created")


def migrate_existing_database(db_path: Path) -> bool:
    """
    Migrate existing database to new schema
    
    This function updates an existing database to support dual tracking
    
    Args:
        db_path: Path to existing SQLite database file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        logger.info("Starting database migration...")
        
        # Check if old issue_trackers table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='issue_trackers'
        """)
        old_table_exists = cursor.fetchone() is not None
        
        if old_table_exists:
            # Check if old table has 'emotion' column (old schema)
            cursor.execute("PRAGMA table_info(issue_trackers)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'emotion' in columns:
                logger.info("Old schema detected. Migrating to dual-tracker system...")
                
                # Rename old table
                cursor.execute("ALTER TABLE issue_trackers RENAME TO issue_trackers_old")
                
                # Create new tables
                _create_emotion_trackers_table(cursor)
                _create_issue_trackers_table(cursor)
                
                # Migrate data: Create emotion trackers
                cursor.execute("""
                    INSERT INTO emotion_trackers (
                        account_id, issue_category, emotion, occurrence_count, 
                        last_occurred, worksheet_completed
                    )
                    SELECT DISTINCT
                        account_id, issue_category, emotion, 
                        occurrence_count, last_occurred, worksheet_completed
                    FROM issue_trackers_old
                    GROUP BY account_id, issue_category, emotion
                """)
                
                # Migrate data: Create issue trackers (sum occurrences per issue_type)
                cursor.execute("""
                    INSERT INTO issue_trackers (
                        account_id, issue_category, issue_type, occurrence_count,
                        last_occurred, worksheet_completed
                    )
                    SELECT 
                        account_id, issue_category, issue_type,
                        COUNT(*) as occurrence_count,
                        MAX(last_occurred) as last_occurred,
                        MAX(worksheet_completed) as worksheet_completed
                    FROM issue_trackers_old
                    GROUP BY account_id, issue_category, issue_type
                """)
                
                # Drop old table
                cursor.execute("DROP TABLE issue_trackers_old")
                
                logger.info("Data migration completed")
        else:
            # Fresh install, just create tables
            _create_emotion_trackers_table(cursor)
            _create_issue_trackers_table(cursor)
        
        # Check and update mental_worksheets table
        cursor.execute("PRAGMA table_info(mental_worksheets)")
        ws_columns = [col[1] for col in cursor.fetchall()]
        
        if 'trigger_type' not in ws_columns:
            logger.info("Updating mental_worksheets table...")
            
            # Rename old table
            cursor.execute("ALTER TABLE mental_worksheets RENAME TO mental_worksheets_old")
            
            # Create new table
            _create_mental_worksheets_table(cursor)
            
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
            
            logger.info("Worksheets table updated")
        
        # Update schema version
        cursor.execute("""
            INSERT OR REPLACE INTO app_metadata (key, value, updated_at)
            VALUES ('schema_version', '2.0.0', datetime('now'))
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Database migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return False

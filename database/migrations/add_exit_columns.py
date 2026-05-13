"""
Add missing exit columns to trades table
"""

from pathlib import Path
from database.connection import get_db_connection
import logging

logger = logging.getLogger(__name__)


def add_exit_columns(db_path: Path):
    """Add missing columns for trade exit data"""
    
    columns_to_add = [
        ("exit_date", "TEXT"),
        ("exit_time", "TEXT"),
        ("multi_exit_price", "REAL"),
        ("target_hit", "INTEGER DEFAULT 0"),
        ("stop_loss_hit", "INTEGER DEFAULT 0"),
        ("mae", "REAL"),
        ("mfe", "REAL"),
        ("trade_duration", "INTEGER"),
        ("total_r", "REAL"),
        ("roe_percentage", "REAL"),
        ("pnl", "REAL DEFAULT 0"),
        ("grade_mentally", "TEXT"),
        ("grade_technically", "TEXT"),
        ("trade_notes_management", "TEXT"),
        ("trade_notes_closing", "TEXT"),
        ("reason_for_closing", "TEXT"),
        ("final_notes", "TEXT"),
        ("commission", "REAL DEFAULT 0"),
    ]
    
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Check existing columns
            cursor.execute("PRAGMA table_info(trades)")
            existing = {row[1] for row in cursor.fetchall()}
            
            # Add missing columns
            for col_name, col_type in columns_to_add:
                if col_name not in existing:
                    try:
                        cursor.execute(f"ALTER TABLE trades ADD COLUMN {col_name} {col_type}")
                        logger.info(f"Added column: {col_name}")
                        print(f"✔ Added column: {col_name}")
                    except Exception as e:
                        logger.error(f"Failed to add {col_name}: {e}")
                        print(f"❌ Failed to add {col_name}: {e}")
            
            print("✔ Migration complete!")
            return True
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    from utils.paths import get_database_path
    db_path = get_database_path()
    add_exit_columns(db_path)

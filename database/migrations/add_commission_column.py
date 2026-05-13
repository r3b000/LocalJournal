"""
Migration: Add commission column to trades table.
Run once: python -m database.migrations.add_commission_column
"""

from pathlib import Path
from database.connection import get_db_connection
from utils.paths import get_database_path
import logging

logger = logging.getLogger(__name__)


def add_commission_column(db_path: Path) -> bool:
    """
    Safely adds 'commission' column to trades table if it doesn't already exist.
    Uses ALTER TABLE — zero risk to existing data.
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()

            # Read current columns
            cursor.execute("PRAGMA table_info(trades)")
            existing_columns = [row[1] for row in cursor.fetchall()]

            if "commission" not in existing_columns:
                cursor.execute("ALTER TABLE trades ADD COLUMN commission REAL DEFAULT 0")
                print("[OK] Added 'commission' column to trades table.")
                logger.info("Migration: Added 'commission' column to trades table.")
            else:
                print("[SKIP] 'commission' column already exists — nothing to do.")
                logger.info("Migration: 'commission' column already present, skipped.")

        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"[ERROR] Migration failed: {e}")
        return False


if __name__ == "__main__":
    db_path = get_database_path()
    print(f"Database path: {db_path}")
    success = add_commission_column(db_path)
    if success:
        print("Migration complete.")
    else:
        print("Migration failed — check logs.")

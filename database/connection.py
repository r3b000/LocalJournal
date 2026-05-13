"""
Database connection management
Handles SQLite connections with proper error handling
"""

import sqlite3
from pathlib import Path
from typing import Optional
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Database connection manager with context support"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
    
    def connect(self) -> sqlite3.Connection:
        """
        Create database connection with proper configuration
        
        Returns:
            SQLite connection object
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
            logger.debug(f"Database connection established: {self.db_path}")
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close(self, conn: sqlite3.Connection):
        """Close database connection"""
        if conn:
            conn.close()
            logger.debug("Database connection closed")


@contextmanager
def get_db_connection(db_path: Path):
    conn = None
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        # ENABLE PERFORMANCE SETTINGS
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")  # Better concurrency
        conn.execute("PRAGMA cache_size = -64000")  # 64MB cache instead of 2MB
        conn.execute("PRAGMA synchronous = NORMAL")  # Faster writes
        conn.execute("PRAGMA temp_store = MEMORY")  # Temp operations in RAM
        
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def execute_query(db_path: Path, query: str, params: tuple = ()) -> bool:
    """
    Execute a query without returning results
    
    Args:
        db_path: Path to database
        query: SQL query
        params: Query parameters
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
        return True
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return False


def fetch_one(db_path: Path, query: str, params: tuple = ()) -> Optional[dict]:
    """
    Fetch single row from database
    
    Args:
        db_path: Path to database
        query: SQL query
        params: Query parameters
        
    Returns:
        Dictionary with row data or None
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Fetch one failed: {e}")
        return None


def fetch_all(db_path: Path, query: str, params: tuple = ()) -> list:
    """
    Fetch all rows from database
    
    Args:
        db_path: Path to database
        query: SQL query
        params: Query parameters
        
    Returns:
        List of dictionaries with row data
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Fetch all failed: {e}")
        return []

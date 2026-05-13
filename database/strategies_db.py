"""
Strategy database operations
Handles CRUD operations for trading strategies
"""

from pathlib import Path
from typing import Optional, List, Dict
import logging
from database.connection import get_db_connection, fetch_one, fetch_all
import streamlit as st

logger = logging.getLogger(__name__)

def create_strategy(db_path: Path, strategy_name: str, description: str = None) -> Optional[int]:
    """
    Create a new trading strategy
    
    Args:
        db_path: Path to database
        strategy_name: Unique strategy name
        description: Optional strategy description
        
    Returns:
        Strategy ID if successful, None otherwise
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO strategies (strategy_name, description)
                VALUES (?, ?)
            """, (strategy_name, description))
            
            strategy_id = cursor.lastrowid
            logger.info(f"Strategy created: {strategy_name} (ID: {strategy_id})")
            
            # Clear cache after creating strategy
            get_all_strategies.clear()
            get_strategy_statistics.clear()
            
            return strategy_id
    except Exception as e:
        logger.error(f"Failed to create strategy: {e}")
        return None

@st.cache_data(ttl=300, show_spinner=False)
def get_all_strategies(db_path: Path) -> List[Dict]:
    """
    Get all strategies
    
    Args:
        db_path: Path to database
        
    Returns:
        List of strategy dictionaries
    """
    query = """
        SELECT strategy_id, strategy_name, description, created_at
        FROM strategies
        ORDER BY strategy_name ASC
    """
    return fetch_all(db_path, query)

def get_strategy_by_id(db_path: Path, strategy_id: int) -> Optional[Dict]:
    """
    Get strategy by ID
    
    Args:
        db_path: Path to database
        strategy_id: Strategy ID
        
    Returns:
        Strategy dictionary or None
    """
    query = """
        SELECT strategy_id, strategy_name, description, created_at
        FROM strategies
        WHERE strategy_id = ?
    """
    return fetch_one(db_path, query, (strategy_id,))

def get_strategy_by_name(db_path: Path, strategy_name: str) -> Optional[Dict]:
    """
    Get strategy by name
    
    Args:
        db_path: Path to database
        strategy_name: Strategy name
        
    Returns:
        Strategy dictionary or None
    """
    query = """
        SELECT strategy_id, strategy_name, description, created_at
        FROM strategies
        WHERE strategy_name = ?
    """
    return fetch_one(db_path, query, (strategy_name,))

def delete_strategy(db_path: Path, strategy_id: int) -> bool:
    """
    Delete strategy (sets strategy_id to NULL in related trades)
    
    Args:
        db_path: Path to database
        strategy_id: Strategy ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # STEP 1: First, set strategy_id to NULL in all related trades
            cursor.execute("""
                UPDATE trades 
                SET strategy_id = NULL 
                WHERE strategy_id = ?
            """, (strategy_id,))
            
            affected_trades = cursor.rowcount
            logger.info(f"Updated {affected_trades} trades to remove strategy reference")
            
            # STEP 2: Now delete the strategy
            cursor.execute("""
                DELETE FROM strategies 
                WHERE strategy_id = ?
            """, (strategy_id,))
            
            if cursor.rowcount > 0:
                logger.info(f"Strategy deleted: ID {strategy_id}")
                
                # Clear cache after deleting strategy
                get_all_strategies.clear()
                get_strategy_statistics.clear()
                
                return True
            else:
                logger.warning(f"Strategy not found: ID {strategy_id}")
                return False
                
    except Exception as e:
        logger.error(f"Failed to delete strategy {strategy_id}: {e}")
        return False

@st.cache_data(ttl=300, show_spinner=False)
def get_strategy_statistics(db_path: Path, strategy_id: int) -> Dict:
    """
    Get statistics for a specific strategy
    
    Args:
        db_path: Path to database
        strategy_id: Strategy ID
        
    Returns:
        Dictionary with strategy statistics
    """
    query = """
        SELECT 
            COUNT(*) as total_trades,
            SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END) as closed_trades,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
            SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
            COALESCE(SUM(pnl), 0) as total_pnl,
            COALESCE(AVG(pnl), 0) as avg_pnl
        FROM trades
        WHERE strategy_id = ? AND status = 'CLOSED'
    """
    
    result = fetch_one(db_path, query, (strategy_id,))
    
    if result:
        closed = result['closed_trades'] or 0
        winning = result['winning_trades'] or 0
        win_rate = (winning / closed * 100) if closed > 0 else 0
        
        return {
            'total_trades': result['total_trades'],
            'closed_trades': closed,
            'winning_trades': winning,
            'losing_trades': result['losing_trades'] or 0,
            'win_rate': win_rate,
            'total_pnl': result['total_pnl'],
            'avg_pnl': result['avg_pnl']
        }
    
    return {
        'total_trades': 0,
        'closed_trades': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'win_rate': 0,
        'total_pnl': 0,
        'avg_pnl': 0
    }

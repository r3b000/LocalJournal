"""
Account database operations
Handles CRUD operations for trading accounts
"""

import streamlit as st
from pathlib import Path
from typing import Optional, List, Dict
import logging
from datetime import datetime
from database.connection import get_db_connection, fetch_one, fetch_all


logger = logging.getLogger(__name__)


def create_account(db_path: Path, account_name: str, starting_equity: float, strategy_description: str = None) -> Optional[int]:
    """
    Create a new trading account
    
    Args:
        db_path: Path to database
        account_name: Unique account name
        starting_equity: Starting equity amount
        strategy_description: Optional strategy description
        
    Returns:
        Account ID if successful, None otherwise
    """
    try:
        # First check if account name already exists
        existing = get_account_by_name(db_path, account_name)
        if existing:
            logger.error(f"Account name '{account_name}' already exists (ID: {existing['account_id']})")
            return None
        
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO accounts (account_name, starting_equity, current_equity, strategy_description)
                VALUES (?, ?, ?, ?)
            """, (account_name, starting_equity, starting_equity, strategy_description))
            
            account_id = cursor.lastrowid
            
            logger.info(f"Account created: {account_name} (ID: {account_id})")
            return account_id
            
    except Exception as e:
        logger.error(f"Failed to create account '{account_name}': {type(e).__name__}: {str(e)}")
        return None


def get_all_accounts(db_path: Path) -> List[Dict]:
    """
    Get all accounts
    
    Args:
        db_path: Path to database
        
    Returns:
        List of account dictionaries
    """
    query = """
        SELECT account_id, account_name, starting_equity, current_equity, 
               strategy_description, created_at, updated_at
        FROM accounts
        ORDER BY created_at DESC
    """
    return fetch_all(db_path, query)


def get_account_by_id(db_path: Path, account_id: int) -> Optional[Dict]:
    """
    Get account by ID
    
    Args:
        db_path: Path to database
        account_id: Account ID
        
    Returns:
        Account dictionary or None
    """
    query = """
        SELECT account_id, account_name, starting_equity, current_equity,
               strategy_description, created_at, updated_at
        FROM accounts
        WHERE account_id = ?
    """
    return fetch_one(db_path, query, (account_id,))


def get_account_by_name(db_path: Path, account_name: str) -> Optional[Dict]:
    """
    Get account by name (case-insensitive)
    
    Args:
        db_path: Path to database
        account_name: Account name
        
    Returns:
        Account dictionary or None
    """
    query = """
        SELECT account_id, account_name, starting_equity, current_equity,
               strategy_description, created_at, updated_at
        FROM accounts
        WHERE LOWER(account_name) = LOWER(?)
    """
    return fetch_one(db_path, query, (account_name,))


def update_account_equity(db_path: Path, account_id: int, new_equity: float) -> bool:
    """
    Update account equity
    
    Args:
        db_path: Path to database
        account_id: Account ID
        new_equity: New equity amount
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE accounts
                SET current_equity = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE account_id = ?
            """, (new_equity, account_id))
            
            if cursor.rowcount > 0:
                logger.info(f"Account equity updated: ID {account_id}, New equity: {new_equity}")
                return True
            return False
            
    except Exception as e:
        logger.error(f"Failed to update account equity: {e}")
        return False


def delete_account(db_path: Path, account_id: int) -> bool:
    """
    Delete account (cascades to trades and mental issues)
    
    Args:
        db_path: Path to database
        account_id: Account ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Get account info before deletion for logging
            cursor.execute("SELECT account_name FROM accounts WHERE account_id = ?", (account_id,))
            account = cursor.fetchone()
            
            if not account:
                logger.warning(f"Account {account_id} not found")
                return False
            
            account_name = account[0]
            
            # Delete account (CASCADE will handle related records)
            cursor.execute("DELETE FROM accounts WHERE account_id = ?", (account_id,))
            
            if cursor.rowcount > 0:
                logger.info(f"Account deleted: '{account_name}' (ID: {account_id})")
                return True
            
            return False
            
    except Exception as e:
        logger.error(f"Failed to delete account {account_id}: {type(e).__name__}: {str(e)}")
        return False


def get_account_stats(db_path: Path, account_id: int) -> Dict:
    """
    Get account statistics
    
    Args:
        db_path: Path to database
        account_id: Account ID
        
    Returns:
        Dictionary with account statistics
    """
    query = """
        SELECT 
            a.current_equity,
            a.starting_equity,
            COUNT(t.trade_id) as total_trades,
            SUM(CASE WHEN t.status = 'OPEN' THEN 1 ELSE 0 END) as open_trades,
            SUM(CASE WHEN t.status = 'CLOSED' THEN 1 ELSE 0 END) as closed_trades,
            COALESCE(SUM(t.pnl), 0) as total_pnl,
            COUNT(CASE WHEN t.pnl > 0 THEN 1 END) as winning_trades,
            CASE 
                WHEN SUM(CASE WHEN t.status = 'CLOSED' THEN 1 ELSE 0 END) > 0
                THEN (COUNT(CASE WHEN t.pnl > 0 THEN 1 END) * 100.0) / SUM(CASE WHEN t.status = 'CLOSED' THEN 1 ELSE 0 END)
                ELSE 0
            END as win_rate
        FROM accounts a
        LEFT JOIN trades t ON a.account_id = t.account_id
        WHERE a.account_id = ?
        GROUP BY a.account_id
    """
    
    result = fetch_one(db_path, query, (account_id,))
    
    if result:
        starting = result['starting_equity']
        current = result['current_equity']
        roi = ((current - starting) / starting * 100) if starting > 0 else 0
        
        return {
            'current_equity': current,
            'starting_equity': starting,
            'total_pnl': result['total_pnl'],
            'roi': roi,
            'total_trades': result['total_trades'],
            'open_trades': result['open_trades'],
            'closed_trades': result['closed_trades'],
            'winning_trades': result.get('winning_trades', 0),
            'win_rate': result.get('win_rate', 0.0)
        }
    
    return {
        'current_equity': 0,
        'starting_equity': 0,
        'total_pnl': 0,
        'roi': 0,
        'total_trades': 0,
        'open_trades': 0,
        'closed_trades': 0,
        'winning_trades': 0,
        'win_rate': 0.0
    }

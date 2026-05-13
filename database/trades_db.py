"""
Trade database operations
Handles CRUD operations for trades
"""

from pathlib import Path
from typing import Optional, List, Dict
import logging
from datetime import datetime
from database.connection import get_db_connection, fetch_one, fetch_all
import streamlit as st


logger = logging.getLogger(__name__)

def create_trade(db_path: Path, trade_data: Dict) -> Optional[int]:
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()

            query = """
                INSERT INTO trades (
                    account_id, symbol, direction, strategy_id,
                    entry_date, entry_time, entry_price,
                    trading_environment, trigger,
                    multi_entry_price, stop_loss, target,
                    risk_amount, risk_percentage, position_size,
                    fta, prospective_r, within_risk_limit,
                    setup_idea, trade_notes_entry,
                    commission,
                    status
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?,
                    ?
                )
            """

            params = (
                trade_data['account_id'],
                trade_data['symbol'],
                trade_data['direction'],
                trade_data.get('strategy_id'),
                trade_data['entry_date'],
                trade_data['entry_time'],
                trade_data['entry_price'],
                trade_data.get('trading_environment'),
                trade_data.get('trigger'),
                trade_data.get('multi_entry_price'),
                trade_data['stop_loss'],
                trade_data.get('target'),
                trade_data['risk_amount'],
                trade_data['risk_percentage'],
                trade_data['position_size'],
                trade_data.get('fta'),
                trade_data.get('prospective_r'),
                trade_data.get('within_risk_limit', True),
                trade_data.get('setup_idea'),
                trade_data.get('trade_notes_entry'),
                trade_data.get('commission', 0.0),
                'OPEN',
            )

            cursor.execute(query, params)
            trade_id = cursor.lastrowid

            logger.info(f"Trade created: ID {trade_id}, {trade_data['symbol']} {trade_data['direction']}")
            return trade_id

    except KeyError as e:
        logger.error(f"Missing required field in trade_data: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to create trade: {type(e).__name__}: {str(e)}")
        return None


def update_trade_exit(db_path: Path, trade_id: int, exit_data: Dict) -> bool:
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT account_id, status FROM trades WHERE trade_id = ?", (trade_id,))
            trade_info = cursor.fetchone()

            if not trade_info:
                logger.error(f"Trade {trade_id} not found")
                return False

            account_id, current_status = trade_info

            if current_status == 'CLOSED':
                logger.warning(f"Trade {trade_id} already closed")
                return False

            # commission is now properly in the SET clause, aligned with params
            query = """
                UPDATE trades SET
                    exit_date               = ?,
                    exit_time               = ?,
                    multi_exit_price        = ?,
                    target_hit              = ?,
                    stop_loss_hit           = ?,
                    mae                     = ?,
                    mfe                     = ?,
                    trade_duration          = ?,
                    total_r                 = ?,
                    roe_percentage          = ?,
                    pnl                     = ?,
                    commission              = ?,
                    grade_mentally          = ?,
                    grade_technically       = ?,
                    trade_notes_management  = ?,
                    trade_notes_closing     = ?,
                    reason_for_closing      = ?,
                    final_notes             = ?,
                    status                  = 'CLOSED',
                    updated_at              = CURRENT_TIMESTAMP
                WHERE trade_id = ?
            """

            params = (
                exit_data.get('exit_date'),
                exit_data.get('exit_time'),
                exit_data.get('multi_exit_price'),
                exit_data.get('target_hit', False),
                exit_data.get('stop_loss_hit', False),
                exit_data.get('mae'),
                exit_data.get('mfe'),
                exit_data.get('trade_duration'),
                exit_data.get('total_r'),
                exit_data.get('roe_percentage'),
                exit_data.get('pnl', 0.0),
                exit_data.get('commission', 0.0),   # now aligned with commission = ? above
                exit_data.get('grade_mentally'),
                exit_data.get('grade_technically'),
                exit_data.get('trade_notes_management'),
                exit_data.get('trade_notes_closing'),
                exit_data.get('reason_for_closing'),
                exit_data.get('final_notes'),
                trade_id,
            )

            cursor.execute(query, params)
            trade_updated = cursor.rowcount > 0

            if not trade_updated:
                logger.error(f"Failed to update trade {trade_id}")
                return False

            # Use net PnL (after commission) for equity update — what you actually made
            pnl_value = exit_data.get('pnl', 0.0)

            cursor.execute("""
                UPDATE accounts
                SET current_equity = current_equity + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE account_id = ?
            """, (pnl_value, account_id))

            equity_updated = cursor.rowcount > 0

            if not equity_updated:
                logger.error(f"Failed to update equity for account {account_id}")
                return False

            cursor.execute("SELECT current_equity FROM accounts WHERE account_id = ?", (account_id,))
            new_equity = cursor.fetchone()

            if new_equity:
                logger.info(f"Trade {trade_id} closed: P&L ${pnl_value:,.2f}, Account {account_id} equity: ${new_equity[0]:,.2f}")

            return True

    except Exception as e:
        logger.error(f"Failed to update trade exit: {type(e).__name__}: {str(e)}")
        return False


def get_trade_by_id(db_path: Path, trade_id: int) -> Optional[Dict]:
    """
    Get trade by ID
    
    Args:
        db_path: Path to database
        trade_id: Trade ID
        
    Returns:
        Trade dictionary or None
    """
    query = "SELECT * FROM trades WHERE trade_id = ?"
    return fetch_one(db_path, query, (trade_id,))


@st.cache_data(ttl=30, show_spinner=False)
def get_all_trades(db_path: Path, account_id: int = None, status: str = None) -> List[Dict]:
    """
    Get all trades with optional filters
    
    Args:
        db_path: Path to database
        account_id: Optional account filter
        status: Optional status filter ('OPEN' or 'CLOSED')
        
    Returns:
        List of trade dictionaries
    """
    query = "SELECT * FROM trades WHERE 1=1"
    params = []
    
    if account_id:
        query += " AND account_id = ?"
        params.append(account_id)
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    query += " ORDER BY entry_date DESC, entry_time DESC"
    
    return fetch_all(db_path, query, tuple(params))


def get_recent_trades(db_path: Path, account_id: int, limit: int = 5) -> List[Dict]:
    """
    Get recent trades for an account
    
    Args:
        db_path: Path to database
        account_id: Account ID
        limit: Number of trades to return
        
    Returns:
        List of trade dictionaries
    """
    query = """
        SELECT * FROM trades
        WHERE account_id = ?
        ORDER BY entry_date DESC, entry_time DESC
        LIMIT ?
    """
    return fetch_all(db_path, query, (account_id, limit))


def get_filtered_trades(db_path: Path, filters: Dict) -> List[Dict]:
    """
    Get trades with multiple filters
    
    Args:
        db_path: Path to database
        filters: Dictionary with filter criteria
            - account_id: int
            - symbol: str
            - direction: str ('LONG' or 'SHORT')
            - status: str ('OPEN' or 'CLOSED')
            - strategy_id: int
            - date_from: str (YYYY-MM-DD)
            - date_to: str (YYYY-MM-DD)
        
    Returns:
        List of trade dictionaries
    """
    query = "SELECT * FROM trades WHERE 1=1"
    params = []
    
    if filters.get('account_id'):
        query += " AND account_id = ?"
        params.append(filters['account_id'])
    
    if filters.get('symbol'):
        query += " AND symbol = ?"
        params.append(filters['symbol'])
    
    if filters.get('direction'):
        query += " AND direction = ?"
        params.append(filters['direction'])
    
    if filters.get('status'):
        query += " AND status = ?"
        params.append(filters['status'])
    
    if filters.get('strategy_id'):
        query += " AND strategy_id = ?"
        params.append(filters['strategy_id'])
    
    if filters.get('date_from'):
        query += " AND entry_date >= ?"
        params.append(filters['date_from'])
    
    if filters.get('date_to'):
        query += " AND entry_date <= ?"
        params.append(filters['date_to'])
    
    query += " ORDER BY entry_date DESC, entry_time DESC"
    
    return fetch_all(db_path, query, tuple(params))


def delete_trade(db_path: Path, trade_id: int) -> bool:
    """
    Delete a trade, revert its P&L from account equity, and cleanup screenshots
    
    Args:
        db_path: Path to database
        trade_id: Trade ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # STEP 1: Get trade info BEFORE deletion
            cursor.execute(
                "SELECT account_id, pnl, status FROM trades WHERE trade_id = ?",
                (trade_id,)
            )
            trade_info = cursor.fetchone()
            
            if not trade_info:
                logger.error(f"Trade {trade_id} not found")
                return False
            
            account_id = trade_info['account_id']
            trade_pnl = trade_info['pnl'] if trade_info['pnl'] is not None else 0.0
            trade_status = trade_info['status']
            
            # STEP 2: If trade was CLOSED, revert P&L from account equity FIRST
            if trade_status == 'CLOSED' and trade_pnl != 0:
                cursor.execute(
                    """
                    UPDATE accounts 
                    SET current_equity = current_equity - ?, 
                        updated_at = CURRENT_TIMESTAMP 
                    WHERE account_id = ?
                    """,
                    (trade_pnl, account_id)
                )
                
                if cursor.rowcount > 0:
                    logger.info(f"Reverted P&L ${trade_pnl:.2f} from account {account_id}")
                else:
                    logger.error(f"Failed to update equity for account {account_id}")
                    return False
            
            # STEP 3: Delete screenshots from database (CASCADE will handle this, but we need file paths)
            cursor.execute("SELECT file_path FROM screenshots WHERE trade_id = ?", (trade_id,))
            screenshot_files = cursor.fetchall()
            
            # STEP 4: Delete the trade (CASCADE will delete screenshot records)
            cursor.execute("DELETE FROM trades WHERE trade_id = ?", (trade_id,))
            
            if cursor.rowcount > 0:
                logger.info(f"Trade {trade_id} deleted successfully from database")
                
                # STEP 5: Delete screenshot files and folder
                try:
                    from utils.paths import get_trade_screenshot_dir
                    import shutil
                    
                    # Delete individual screenshot files
                    deleted_files = 0
                    for screenshot in screenshot_files:
                        file_path = Path(screenshot['file_path'])
                        if file_path.exists():
                            try:
                                file_path.unlink()
                                deleted_files += 1
                            except Exception as e:
                                logger.warning(f"Failed to delete screenshot file {file_path}: {e}")
                    
                    # Delete the entire trade screenshot folder
                    screenshot_dir = get_trade_screenshot_dir(trade_id)
                    if screenshot_dir.exists():
                        try:
                            shutil.rmtree(screenshot_dir)
                            logger.info(f"Deleted screenshot folder: {screenshot_dir}")
                        except Exception as e:
                            logger.warning(f"Failed to delete screenshot folder {screenshot_dir}: {e}")
                    
                    if deleted_files > 0:
                        logger.info(f"Deleted {deleted_files} screenshot file(s) for trade {trade_id}")
                    
                except Exception as e:
                    logger.warning(f"Failed to cleanup screenshots for trade {trade_id}: {e}")
                
                return True
            
            return False
            
    except Exception as e:
        logger.error(f"Failed to delete trade: {e}")
        return False


def add_screenshot(
    db_path: Path,
    trade_id: int,
    screenshot_type: str,
    file_path: str,
    category: str = None
) -> Optional[int]:
    """
    Add screenshot to trade
    
    Args:
        db_path: Path to database
        trade_id: Trade ID
        screenshot_type: Type ('ENTRY', 'EXIT', 'OTHER')
        file_path: Path to screenshot file
        category: Screenshot category (optional) - 'Chart', 'P&L', 'Indicators', etc.
        
    Returns:
        Screenshot ID if successful, None otherwise
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if screenshot_category column exists (backward compatibility)
            cursor.execute("PRAGMA table_info(screenshots)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'screenshot_category' in columns:
                # New schema with category support
                cursor.execute("""
                    INSERT INTO screenshots (trade_id, screenshot_type, screenshot_category, file_path)
                    VALUES (?, ?, ?, ?)
                """, (trade_id, screenshot_type, category, file_path))
            else:
                # Old schema without category
                cursor.execute("""
                    INSERT INTO screenshots (trade_id, screenshot_type, file_path)
                    VALUES (?, ?, ?)
                """, (trade_id, screenshot_type, file_path))
                
                logger.warning("screenshot_category column not found - consider running database migration")
            
            screenshot_id = cursor.lastrowid
            logger.info(f"Screenshot added: Trade {trade_id}, Type {screenshot_type}, Category {category}")
            return screenshot_id
            
    except Exception as e:
        logger.error(f"Failed to add screenshot: {e}")
        return None

def get_trade_screenshots(db_path: Path, trade_id: int) -> List[Dict]:
    """
    Get all screenshots for a trade with categories
    
    Args:
        db_path: Path to database
        trade_id: Trade ID
        
    Returns:
        List of screenshot dictionaries with categories
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if screenshot_category column exists
            cursor.execute("PRAGMA table_info(screenshots)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'screenshot_category' in columns:
                # New schema with category
                query = """
                    SELECT screenshot_id, trade_id, screenshot_type, screenshot_category, file_path, uploaded_at
                    FROM screenshots
                    WHERE trade_id = ?
                    ORDER BY screenshot_type, uploaded_at ASC
                """
            else:
                # Old schema without category
                query = """
                    SELECT screenshot_id, trade_id, screenshot_type, file_path, uploaded_at
                    FROM screenshots
                    WHERE trade_id = ?
                    ORDER BY screenshot_type, uploaded_at ASC
                """
            
            cursor.execute(query, (trade_id,))
            
            # Fetch results and convert to dictionaries
            rows = cursor.fetchall()
            
            if not rows:
                return []
            
            # Get column names
            column_names = [description[0] for description in cursor.description]
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                screenshot_dict = dict(zip(column_names, row))
                
                # Add default category if not present
                if 'screenshot_category' not in screenshot_dict:
                    screenshot_dict['screenshot_category'] = 'Other'
                
                results.append(screenshot_dict)
            
            return results
            
    except Exception as e:
        logger.error(f"Failed to get trade screenshots: {e}")
        return []


def delete_screenshot(db_path: Path, screenshot_id: int) -> bool:
    """
    Delete a screenshot
    
    Args:
        db_path: Path to database
        screenshot_id: Screenshot ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Get file path before deletion (for file cleanup)
            cursor.execute("SELECT file_path FROM screenshots WHERE screenshot_id = ?", (screenshot_id,))
            result = cursor.fetchone()
            
            if result:
                file_path = result[0]
                
                # Delete from database
                cursor.execute("DELETE FROM screenshots WHERE screenshot_id = ?", (screenshot_id,))
                
                # Try to delete file
                try:
                    Path(file_path).unlink(missing_ok=True)
                    logger.info(f"Screenshot deleted: ID {screenshot_id}, File: {file_path}")
                except Exception as file_err:
                    logger.warning(f"Failed to delete screenshot file: {file_err}")
                
                return True
            else:
                logger.warning(f"Screenshot {screenshot_id} not found")
                return False
                
    except Exception as e:
        logger.error(f"Failed to delete screenshot: {e}")
        return False


def get_all_screenshots_by_type(db_path: Path, trade_id: int, screenshot_type: str) -> List[Dict]:
    """
    Get all screenshots of a specific type for a trade
    
    Args:
        db_path: Path to database
        trade_id: Trade ID
        screenshot_type: 'ENTRY' or 'EXIT'
        
    Returns:
        List of screenshot dictionaries
    """
    try:
        screenshots = get_trade_screenshots(db_path, trade_id)
        return [ss for ss in screenshots if ss.get('screenshot_type') == screenshot_type]
    except Exception as e:
        logger.error(f"Failed to get screenshots by type: {e}")
        return []


def migrate_screenshots_table(db_path: Path) -> bool:
    """
    Migrate screenshots table to add category column if missing
    
    Returns:
        bool: True if successful or already migrated
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if column exists
            cursor.execute("PRAGMA table_info(screenshots)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'screenshot_category' not in columns:
                logger.info("Migrating screenshots table to add screenshot_category column...")
                
                cursor.execute("""
                    ALTER TABLE screenshots
                    ADD COLUMN screenshot_category TEXT
                """)
                
                logger.info("✔ Screenshots table migrated successfully")
                return True
            else:
                logger.info("✔ Screenshots table already has screenshot_category column")
                return True
                
    except Exception as e:
        logger.error(f"Failed to migrate screenshots table: {e}")
        return False



def verify_trades_table_schema(db_path: Path) -> Dict:
    """
    Verify the trades table has all required columns
    
    Returns:
        Dictionary with schema info
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(trades)")
            columns = cursor.fetchall()
            
            column_names = [col[1] for col in columns]
            
            required_columns = [
                'trade_id', 'account_id', 'symbol', 'direction', 'status',
                'entry_date', 'entry_time', 'entry_price',
                'exit_date', 'exit_time', 'multi_exit_price',
                'stop_loss', 'target', 'risk_amount', 'risk_percentage',
                'position_size', 'pnl', 'total_r', 'roe_percentage',
                'trade_duration', 'target_hit', 'stop_loss_hit',
                'mae', 'mfe', 'grade_mentally', 'grade_technically',
                'trade_notes_management', 'trade_notes_closing',
                'reason_for_closing', 'final_notes'
            ]
            
            missing = [col for col in required_columns if col not in column_names]
            
            return {
                'exists': True,
                'columns': column_names,
                'missing': missing,
                'ok': len(missing) == 0
            }
    except Exception as e:
        logger.error(f"Failed to verify schema: {e}")
        return {'exists': False, 'error': str(e)}


def update_trade_open_fields(db_path: Path, trade_id: int, fields: dict) -> bool:
    """Update editable fields on an OPEN trade."""
    allowed = {
        'symbol', 'direction', 'strategy_id', 'entry_date', 'entry_time',
        'entry_price', 'multi_entry_price', 'trading_environment', 'trigger',
        'stop_loss', 'target', 'risk_amount', 'risk_percentage', 'position_size',
        'fta', 'prospective_r', 'within_risk_limit', 'setup_idea',
        'trade_notes_entry', 'commission'
    }
    safe = {k: v for k, v in fields.items() if k in allowed}
    if not safe:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in safe)
    values = list(safe.values()) + [trade_id]
    try:
        with get_db_connection(db_path) as conn:
            conn.execute(
                f"UPDATE trades SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE trade_id = ? AND status = 'OPEN'",
                values
            )
        return True
    except Exception as e:
        logger.error(f"update_trade_open_fields failed: {e}")
        return False

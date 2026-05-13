"""
Statistics Database Operations
Handles all database queries for statistics and analytics
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from contextlib import contextmanager
from datetime import datetime, timedelta
import streamlit as st
from database.accounts_db import get_account_by_id


logger = logging.getLogger(__name__)



@st.cache_data(ttl=60, show_spinner=False)
def get_all_statistics_batch(db_path_str: str, account_id: int, date_from: str = None, date_to: str = None) -> Dict:
    """
    PERFORMANCE OPTIMIZED: Load all statistics data in single batch
    
    Args:
        db_path_str: Database path as string (for Streamlit caching)
        account_id: Account ID
        date_from: Optional start date filter
        date_to: Optional end date filter
    
    Returns:
        Dictionary containing all statistics data
    """
    from pathlib import Path
    db_path = Path(db_path_str)
    
    # Load all data
    return {
        'metrics': get_performance_metrics(db_path, account_id, date_from, date_to),
        'distribution': get_trade_distribution(db_path, account_id, 0.5),
        'by_symbol': get_performance_by_symbol(db_path, account_id),
        'by_strategy': get_performance_by_strategy(db_path, account_id),
        'by_direction': get_performance_by_direction(db_path, account_id),
        'all_trades': get_all_closed_trades(db_path, account_id)
    }





# =============================================================================
# DATABASE CONNECTION HELPER
# =============================================================================

@contextmanager
def get_db_connection(db_path: Path):
    """
    Context manager for database connections
    
    Args:
        db_path: Path to database file
        
    Yields:
        Database connection object
    """
    conn = None
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def fetch_all(db_path: Path, query: str, params: tuple = ()) -> List[Dict]:
    """
    Execute query and fetch all results as list of dictionaries
    
    Args:
        db_path: Path to database
        query: SQL query string
        params: Query parameters tuple
        
    Returns:
        List of dictionaries with query results
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            columns = [description[0] for description in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    except Exception as e:
        logger.error(f"Query execution error: {e}")
        return []


# =============================================================================
# PERFORMANCE METRICS
# =============================================================================

@st.cache_data(ttl=60, show_spinner=False)
def get_performance_metrics(db_path: Path, account_id: int, 
                           date_from: Optional[str] = None, 
                           date_to: Optional[str] = None) -> Dict:
    """
    Get comprehensive performance metrics for an account
    
    Args:
        db_path: Path to database
        account_id: Account ID
        date_from: Optional start date (YYYY-MM-DD)
        date_to: Optional end date (YYYY-MM-DD)
        
    Returns:
        Dictionary with performance metrics
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Build query with date filters
            date_filter = ""
            params = [account_id]
            
            if date_from:
                date_filter += " AND entry_date >= ?"
                params.append(date_from)
            
            if date_to:
                date_filter += " AND entry_date <= ?"
                params.append(date_to)
            
            # Get trade statistics
            query = f"""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END) as closed_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(CASE WHEN pnl = 0 THEN 1 ELSE 0 END) as breakeven_trades,
                    COALESCE(SUM(pnl), 0) as total_pnl,
                    COALESCE(SUM(CASE WHEN pnl > 0 THEN pnl END), 0) as total_profit,
                    COALESCE(SUM(CASE WHEN pnl < 0 THEN ABS(pnl) END), 0) as total_loss,
                    COALESCE(AVG(CASE WHEN pnl > 0 THEN pnl END), 0) as avg_win,
                    COALESCE(AVG(CASE WHEN pnl < 0 THEN pnl END), 0) as avg_loss,
                    COALESCE(AVG(CASE WHEN status = 'CLOSED' AND total_r IS NOT NULL AND total_r != 0 THEN total_r END), 0) as avg_r,
                    COALESCE(MAX(total_r), 0) as best_r,
                    COALESCE(MIN(total_r), 0) as worst_r,
                    COALESCE(AVG(trade_duration), 0) as avg_duration
                FROM trades
                WHERE account_id = ? AND status = 'CLOSED'{date_filter}
            """
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            if not result:
                return _get_empty_metrics()
            
            # Extract values
            total_trades = result[0] or 0
            closed_trades = result[1] or 0
            winning_trades = result[2] or 0
            losing_trades = result[3] or 0
            breakeven_trades = result[4] or 0
            total_pnl = result[5] or 0.0
            total_profit = result[6] or 0.0
            total_loss = result[7] or 0.0
            avg_win = result[8] or 0.0
            avg_loss = result[9] or 0.0
            avg_r = result[10] or 0.0
            best_r = result[11] or 0.0
            worst_r = result[12] or 0.0
            avg_duration = result[13] or 0.0
            
            # Calculate derived metrics
            win_rate = (winning_trades / closed_trades * 100) if closed_trades > 0 else 0.0
            
            profit_factor = (total_profit / total_loss) if total_loss > 0 else 0.0
            
            # Expectancy = (Win% × AvgWin) - (Loss% × AvgLoss)
            loss_rate = (losing_trades / closed_trades * 100) if closed_trades > 0 else 0.0
            expectancy = ((win_rate / 100) * avg_win) - ((loss_rate / 100) * abs(avg_loss))
            
            return {
                'total_trades': total_trades,
                'closed_trades': closed_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'breakeven_trades': breakeven_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'total_profit': total_profit,
                'total_loss': total_loss,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'expectancy': expectancy,
                'avg_r': avg_r,
                'best_r': best_r,
                'worst_r': worst_r,
                'avg_duration': avg_duration
            }
            
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        return _get_empty_metrics()


# =============================================================================
# CALENDAR DATA
# =============================================================================
@st.cache_data(ttl=60, show_spinner=False)
def get_daily_pnl_calendar(db_path: Path, account_id: int, year: int, month: int) -> dict:
    """
    Get daily P&L data for calendar view.
    FIXED: Groups by exit_date (not entry_date) so P&L only appears
    on the day the trade was actually CLOSED.
    """
    try:
        start_date = f"{year}-{month:02d}-01"

        if month == 12:
            end_date = f"{year}-12-31"
        else:
            next_month = datetime(year, month, 1) + timedelta(days=32)
            end_date   = datetime(year, month, 1).replace(
                day=1, month=next_month.month
            ) - timedelta(days=1)
            end_date   = end_date.strftime("%Y-%m-%d")

        # FIXED: use exit_date, require status=CLOSED and exit_date NOT NULL
        query = """
            SELECT
                exit_date,
                COUNT(*)                                        as trade_count,
                SUM(pnl)                                        as daily_pnl,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)       as wins,
                SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END)       as losses
            FROM trades
            WHERE account_id = ?
              AND status     = 'CLOSED'
              AND exit_date  IS NOT NULL
              AND exit_date  BETWEEN ? AND ?
            GROUP BY exit_date
            ORDER BY exit_date
        """

        results = fetch_all(db_path, query, (account_id, start_date, end_date))

        calendar_data = {}
        for row in results:
            date_str    = row['exit_date']          # key is now exit_date
            trade_count = row['trade_count'] or 0
            daily_pnl   = row['daily_pnl']   or 0.0
            wins        = row['wins']         or 0
            losses      = row['losses']       or 0
            win_rate    = (wins / trade_count * 100) if trade_count > 0 else 0.0

            calendar_data[date_str] = {
                'pnl':         daily_pnl,
                'trade_count': trade_count,
                'wins':        wins,
                'losses':      losses,
                'win_rate':    win_rate
            }

        return calendar_data

    except Exception as e:
        logger.error(f"Failed to get calendar data: {e}")
        return {}



# =============================================================================
# TRADE DISTRIBUTION
# =============================================================================

@st.cache_data(ttl=60, show_spinner=False)
def get_trade_distribution(db_path: Path, account_id: int, breakeven_threshold: float = 1.0) -> Dict:
    """
    Get trade distribution for pie chart (Win/Loss/Breakeven)
    
    Args:
        db_path: Path to database
        account_id: Account ID
        breakeven_threshold: P&L threshold for breakeven (default $1)
        
    Returns:
        Dictionary with distribution data
    """
    try:
        query = """
            SELECT 
                pnl,
                trade_id
            FROM trades
            WHERE account_id = ? AND status = 'CLOSED'
        """
        
        results = fetch_all(db_path, query, (account_id,))
        
        wins = []
        losses = []
        breakevens = []
        
        for row in results:
            pnl = row['pnl'] or 0.0
            
            if pnl > breakeven_threshold:
                wins.append(pnl)
            elif pnl < -breakeven_threshold:
                losses.append(pnl)
            else:
                breakevens.append(pnl)
        
        win_count = len(wins)
        loss_count = len(losses)
        breakeven_count = len(breakevens)
        total = win_count + loss_count + breakeven_count
        
        return {
            'wins': {
                'count': win_count,
                'percentage': (win_count / total * 100) if total > 0 else 0.0,
                'total_pnl': sum(wins)
            },
            'losses': {
                'count': loss_count,
                'percentage': (loss_count / total * 100) if total > 0 else 0.0,
                'total_pnl': sum(losses)
            },
            'breakevens': {
                'count': breakeven_count,
                'percentage': (breakeven_count / total * 100) if total > 0 else 0.0,
                'total_pnl': sum(breakevens)
            },
            'total_trades': total
        }
        
    except Exception as e:
        logger.error(f"Failed to get trade distribution: {e}")
        return {
            'wins': {'count': 0, 'percentage': 0.0, 'total_pnl': 0.0},
            'losses': {'count': 0, 'percentage': 0.0, 'total_pnl': 0.0},
            'breakevens': {'count': 0, 'percentage': 0.0, 'total_pnl': 0.0},
            'total_trades': 0
        }


# =============================================================================
# EQUITY CURVE
# =============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def get_equity_curve_data(db_path: Path, account_id: int) -> List[Dict]:
    """
    Get equity curve data using SQL window function (10x faster than Python loop)
    
    Args:
        db_path: Path to database
        account_id: Account ID
        
    Returns:
        List of equity curve points
    """
    # Get starting equity
    account = get_account_by_id(db_path, account_id)
    if not account:
        return []
    
    starting_equity = account['starting_equity']
    
    # Use SQL window function for running total (much faster than Python loop)
    query = """
        WITH running_equity AS (
            SELECT 
                trade_id,
                exit_date,
                exit_time,
                pnl,
                symbol,
                direction,
                SUM(pnl) OVER (
                    ORDER BY exit_date, exit_time 
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) as cumulative_pnl
            FROM trades
            WHERE account_id = ? AND status = 'CLOSED'
            ORDER BY exit_date, exit_time
        )
        SELECT 
            trade_id,
            exit_date,
            exit_time,
            pnl,
            symbol,
            direction,
            (? + cumulative_pnl) as equity
        FROM running_equity
    """
    
    return fetch_all(db_path, query, (account_id, starting_equity))

# =============================================================================
# STREAK DATA
# =============================================================================

def get_streak_data(db_path: Path, account_id: int) -> Dict:
    """
    Get win/loss streak data
    
    Args:
        db_path: Path to database
        account_id: Account ID
        
    Returns:
        Dictionary with streak statistics
    """
    try:
        query = """
            SELECT pnl
            FROM trades
            WHERE account_id = ? AND status = 'CLOSED'
            ORDER BY exit_date ASC, exit_time ASC
        """
        
        results = fetch_all(db_path, query, (account_id,))
        
        if not results:
            return _get_empty_streak_data()
        
        # Calculate streaks
        current_streak = 0
        current_streak_type = None
        
        best_win_streak = 0
        worst_loss_streak = 0
        
        temp_win_streak = 0
        temp_loss_streak = 0
        
        all_win_streaks = []
        all_loss_streaks = []
        
        for row in results:
            pnl = row['pnl'] or 0.0
            
            if pnl > 0:
                # Winning trade
                temp_win_streak += 1
                
                if temp_loss_streak > 0:
                    all_loss_streaks.append(temp_loss_streak)
                    temp_loss_streak = 0
                
                if temp_win_streak > best_win_streak:
                    best_win_streak = temp_win_streak
                
                current_streak_type = 'win'
            elif pnl < 0:
                # Losing trade
                temp_loss_streak += 1
                
                if temp_win_streak > 0:
                    all_win_streaks.append(temp_win_streak)
                    temp_win_streak = 0
                
                if temp_loss_streak > worst_loss_streak:
                    worst_loss_streak = temp_loss_streak
                
                current_streak_type = 'loss'
        
        # Add final streak
        if temp_win_streak > 0:
            all_win_streaks.append(temp_win_streak)
            current_streak = temp_win_streak
        elif temp_loss_streak > 0:
            all_loss_streaks.append(temp_loss_streak)
            current_streak = -temp_loss_streak
        
        # Calculate averages
        avg_win_streak = sum(all_win_streaks) / len(all_win_streaks) if all_win_streaks else 0.0
        avg_loss_streak = sum(all_loss_streaks) / len(all_loss_streaks) if all_loss_streaks else 0.0
        
        return {
            'current_streak': current_streak,
            'current_streak_type': current_streak_type,
            'best_win_streak': best_win_streak,
            'worst_loss_streak': worst_loss_streak,
            'avg_win_streak': avg_win_streak,
            'avg_loss_streak': avg_loss_streak
        }
        
    except Exception as e:
        logger.error(f"Failed to get streak data: {e}")
        return _get_empty_streak_data()


# =============================================================================
# PERFORMANCE HEATMAP
# =============================================================================

def get_performance_heatmap(db_path: Path, account_id: int) -> Dict:
    """
    Get performance heatmap data (day of week analysis)
    
    Args:
        db_path: Path to database
        account_id: Account ID
        
    Returns:
        Dictionary with day-of-week performance
    """
    try:
        query = """
            SELECT 
                entry_date,
                pnl
            FROM trades
            WHERE account_id = ? AND status = 'CLOSED'
        """
        
        results = fetch_all(db_path, query, (account_id,))
        
        # Initialize day-of-week data
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = {day: {'trades': [], 'pnl': []} for day in days}
        
        for row in results:
            date_str = row['entry_date']
            pnl = row['pnl'] or 0.0
            
            # Parse date and get day of week
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                day_name = days[date_obj.weekday()]
                
                heatmap_data[day_name]['trades'].append(1)
                heatmap_data[day_name]['pnl'].append(pnl)
            except:
                continue
        
        # Calculate statistics for each day
        result = {}
        
        for day in days:
            trades = heatmap_data[day]['trades']
            pnls = heatmap_data[day]['pnl']
            
            trade_count = len(trades)
            total_pnl = sum(pnls)
            avg_pnl = total_pnl / trade_count if trade_count > 0 else 0.0
            wins = sum(1 for p in pnls if p > 0)
            win_rate = (wins / trade_count * 100) if trade_count > 0 else 0.0
            
            result[day] = {
                'trade_count': trade_count,
                'total_pnl': total_pnl,
                'avg_pnl': avg_pnl,
                'win_rate': win_rate
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get heatmap data: {e}")
        return {}


# =============================================================================
# RISK METRICS
# =============================================================================

def get_risk_metrics(db_path: Path, account_id: int) -> Dict:
    """
    Calculate risk metrics (Sharpe, Calmar, Recovery Factor)
    
    Args:
        db_path: Path to database
        account_id: Account ID
        
    Returns:
        Dictionary with risk metrics
    """
    try:
        # Get equity curve data
        equity_data, starting_equity, max_drawdown_pct = get_equity_curve_data(db_path, account_id)
        
        if not equity_data:
            return _get_empty_risk_metrics()
        
        # Extract P&L values
        pnls = [trade['pnl'] for trade in equity_data]
        
        # Calculate metrics
        total_pnl = sum(pnls)
        trade_count = len(pnls)
        
        # Average return per trade
        avg_return = total_pnl / trade_count if trade_count > 0 else 0.0
        
        # Standard deviation of returns
        if trade_count > 1:
            variance = sum((pnl - avg_return) ** 2 for pnl in pnls) / (trade_count - 1)
            std_dev = variance ** 0.5
        else:
            std_dev = 0.0
        
        # Sharpe Ratio = (Average Return - Risk Free Rate) / Std Dev
        # Assuming risk-free rate = 0 for simplicity
        sharpe_ratio = (avg_return / std_dev) if std_dev > 0 else 0.0
        
        # Calculate max drawdown in dollars
        max_drawdown_dollars = (max_drawdown_pct / 100) * starting_equity if starting_equity > 0 else 0.0
        
        # Calmar Ratio = Total Return / Max Drawdown
        total_return_pct = (total_pnl / starting_equity * 100) if starting_equity > 0 else 0.0
        calmar_ratio = (total_return_pct / max_drawdown_pct) if max_drawdown_pct > 0 else 0.0
        
        # Recovery Factor = Net Profit / Max Drawdown (in dollars)
        recovery_factor = (total_pnl / max_drawdown_dollars) if max_drawdown_dollars > 0 else 0.0
        
        # Find maximum consecutive drawdown
        peak = starting_equity
        max_dd_consecutive = 0.0
        
        for trade in equity_data:
            equity = trade['equity']
            if equity > peak:
                peak = equity
            
            dd = ((peak - equity) / peak * 100) if peak > 0 else 0.0
            if dd > max_dd_consecutive:
                max_dd_consecutive = dd
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown_pct,
            'max_drawdown_dollars': max_drawdown_dollars,
            'calmar_ratio': calmar_ratio,
            'recovery_factor': recovery_factor,
            'total_return_pct': total_return_pct,
            'std_dev': std_dev
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate risk metrics: {e}")
        return _get_empty_risk_metrics()


# =============================================================================
# PERFORMANCE BY FILTERS
# =============================================================================

@st.cache_data(ttl=60, show_spinner=False)
def get_performance_by_symbol(db_path: Path, account_id: int) -> List[Dict]:
    """Get performance broken down by symbol"""
    query = """
        SELECT 
            symbol,
            COUNT(*) as trades,
            SUM(pnl) as total_pnl,
            AVG(pnl) as avg_pnl,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins
        FROM trades
        WHERE account_id = ? AND status = 'CLOSED'
        GROUP BY symbol
        ORDER BY total_pnl DESC
    """
    
    results = fetch_all(db_path, query, (account_id,))
    
    performance = []
    for row in results:
        trades = row['trades'] or 0
        wins = row['wins'] or 0
        win_rate = (wins / trades * 100) if trades > 0 else 0.0
        
        performance.append({
            'symbol': row['symbol'],
            'trades': trades,
            'total_pnl': row['total_pnl'] or 0.0,
            'avg_pnl': row['avg_pnl'] or 0.0,
            'win_rate': win_rate
        })
    
    return performance

@st.cache_data(ttl=60, show_spinner=False)
def get_performance_by_strategy(db_path: Path, account_id: int) -> List[Dict]:
    """Get performance broken down by strategy"""
    query = """
        SELECT 
            COALESCE(s.strategy_name, 'No Strategy') as strategy_name,
            COUNT(*) as trades,
            SUM(t.pnl) as total_pnl,
            AVG(t.pnl) as avg_pnl,
            SUM(CASE WHEN t.pnl > 0 THEN 1 ELSE 0 END) as wins
        FROM trades t
        LEFT JOIN strategies s ON t.strategy_id = s.strategy_id
        WHERE t.account_id = ? AND t.status = 'CLOSED'
        GROUP BY s.strategy_name
        ORDER BY total_pnl DESC
    """
    
    results = fetch_all(db_path, query, (account_id,))
    
    performance = []
    for row in results:
        trades = row['trades'] or 0
        wins = row['wins'] or 0
        win_rate = (wins / trades * 100) if trades > 0 else 0.0
        
        performance.append({
            'strategy_name': row['strategy_name'],
            'trades': trades,
            'total_pnl': row['total_pnl'] or 0.0,
            'avg_pnl': row['avg_pnl'] or 0.0,
            'win_rate': win_rate
        })
    
    return performance


@st.cache_data(ttl=60, show_spinner=False)
def get_performance_by_direction(db_path: Path, account_id: int) -> Dict:
    """Get performance broken down by direction"""
    query = """
        SELECT 
            direction,
            COUNT(*) as trades,
            SUM(pnl) as total_pnl,
            AVG(pnl) as avg_pnl,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins
        FROM trades
        WHERE account_id = ? AND status = 'CLOSED'
        GROUP BY direction
    """
    
    results = fetch_all(db_path, query, (account_id,))
    
    performance = {'LONG': None, 'SHORT': None}
    
    for row in results:
        direction = row['direction']
        trades = row['trades'] or 0
        wins = row['wins'] or 0
        win_rate = (wins / trades * 100) if trades > 0 else 0.0
        
        performance[direction] = {
            'trades': trades,
            'wins': wins,
            'total_pnl': row['total_pnl'] or 0.0,
            'avg_pnl': row['avg_pnl'] or 0.0,
            'win_rate': win_rate
        }
    
    return performance


# =============================================================================
# ALL TRADES
# =============================================================================

def get_all_closed_trades(db_path: Path, account_id: int) -> List[Dict]:
    """
    Get all closed trades for an account
    
    Args:
        db_path: Path to database
        account_id: Account ID
        
    Returns:
        List of trade dictionaries
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM trades
                WHERE account_id = ? AND status = 'CLOSED'
                ORDER BY exit_date DESC, exit_time DESC
            """
            
            cursor.execute(query, (account_id,))
            
            columns = [description[0] for description in cursor.description]
            trades = []
            
            for row in cursor.fetchall():
                trade_dict = dict(zip(columns, row))
                trades.append(trade_dict)
            
            return trades
            
    except Exception as e:
        logger.error(f"Failed to get all closed trades: {e}")
        return []


# =============================================================================
# LEGACY FUNCTIONS
# =============================================================================

def get_calendar_data(db_path: Path, account_id: int) -> Dict:
    """Legacy function - redirects to get_daily_pnl_calendar"""
    from datetime import datetime
    now = datetime.now()
    return get_daily_pnl_calendar(db_path, account_id, now.year, now.month)


# =============================================================================
# HELPER FUNCTIONS FOR EMPTY DATA
# =============================================================================

def _get_empty_metrics() -> Dict:
    """Return empty metrics structure"""
    return {
        'total_trades': 0,
        'closed_trades': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'breakeven_trades': 0,
        'win_rate': 0.0,
        'total_pnl': 0.0,
        'total_profit': 0.0,
        'total_loss': 0.0,
        'avg_win': 0.0,
        'avg_loss': 0.0,
        'profit_factor': 0.0,
        'expectancy': 0.0,
        'avg_r': 0.0,
        'best_r': 0.0,
        'worst_r': 0.0,
        'avg_duration': 0.0
    }


def _get_empty_streak_data() -> Dict:
    """Return empty streak data structure"""
    return {
        'current_streak': 0,
        'current_streak_type': None,
        'best_win_streak': 0,
        'worst_loss_streak': 0,
        'avg_win_streak': 0.0,
        'avg_loss_streak': 0.0
    }


def _get_empty_risk_metrics() -> Dict:
    """Return empty risk metrics structure"""
    return {
        'sharpe_ratio': 0.0,
        'max_drawdown_pct': 0.0,
        'max_drawdown_dollars': 0.0,
        'calmar_ratio': 0.0,
        'recovery_factor': 0.0,
        'total_return_pct': 0.0,
        'std_dev': 0.0
    }


 # Add this to your statistics_db.py file

def get_trades_by_filter(db_path: Path, account_id: int, filter_type: str, filter_value: str = None) -> List[Dict]:
    """
    Get trades filtered by specific criteria - optimized with direct SQL filtering
    
    Args:
        db_path: Path to database
        account_id: Account ID
        filter_type: Type of filter ('symbol', 'strategy', 'direction', 'grade_mental', 'grade_technical', 'all')
        filter_value: Value to filter by (optional for 'all')
        
    Returns:
        List of trade dictionaries
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Base query
            base_query = """
                SELECT 
                    t.*,
                    s.strategy_name
                FROM trades t
                LEFT JOIN strategies s ON t.strategy_id = s.strategy_id
                WHERE t.account_id = ? AND t.status = 'CLOSED'
            """
            
            params = [account_id]
            
            # Add filter conditions
            if filter_type == 'symbol' and filter_value:
                base_query += " AND t.symbol = ?"
                params.append(filter_value)
            elif filter_type == 'strategy' and filter_value:
                if filter_value == 'No Strategy':
                    base_query += " AND (s.strategy_name IS NULL OR s.strategy_name = 'No Strategy')"
                else:
                    base_query += " AND s.strategy_name = ?"
                    params.append(filter_value)
            elif filter_type == 'direction' and filter_value:
                base_query += " AND t.direction = ?"
                params.append(filter_value)
            elif filter_type == 'grade_mental' and filter_value:
                base_query += " AND t.grade_mental = ?"
                params.append(filter_value)
            elif filter_type == 'grade_technical' and filter_value:
                base_query += " AND t.grade_technical = ?"
                params.append(filter_value)
            
            base_query += " ORDER BY t.exit_date DESC, t.exit_time DESC LIMIT 1000"
            
            cursor.execute(base_query, params)
            
            columns = [description[0] for description in cursor.description]
            trades = []
            
            for row in cursor.fetchall():
                trade_dict = dict(zip(columns, row))
                trades.append(trade_dict)
            
            return trades
            
    except Exception as e:
        logger.error(f"Failed to get filtered trades: {e}")
        return []


def get_unique_filter_values(db_path: Path, account_id: int, filter_type: str) -> List[str]:
    """
    Get unique values for a filter type - optimized with direct SQL
    
    Args:
        db_path: Path to database
        account_id: Account ID
        filter_type: Type of filter ('symbol', 'strategy', 'direction', 'grade_mental', 'grade_technical')
        
    Returns:
        List of unique values
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            if filter_type == 'symbol':
                query = """
                    SELECT DISTINCT symbol 
                    FROM trades 
                    WHERE account_id = ? AND status = 'CLOSED' AND symbol IS NOT NULL
                    ORDER BY symbol
                """
                cursor.execute(query, (account_id,))
                
            elif filter_type == 'strategy':
                query = """
                    SELECT DISTINCT COALESCE(s.strategy_name, 'No Strategy') as strategy_name
                    FROM trades t
                    LEFT JOIN strategies s ON t.strategy_id = s.strategy_id
                    WHERE t.account_id = ? AND t.status = 'CLOSED'
                    ORDER BY strategy_name
                """
                cursor.execute(query, (account_id,))
                
            elif filter_type == 'direction':
                return ['LONG', 'SHORT']
                
            elif filter_type == 'grade_mental':
                query = """
                    SELECT DISTINCT grade_mental 
                    FROM trades 
                    WHERE account_id = ? AND status = 'CLOSED' 
                    AND grade_mental IS NOT NULL 
                    AND grade_mental != 'N/A'
                    ORDER BY grade_mental
                """
                cursor.execute(query, (account_id,))
                
            elif filter_type == 'grade_technical':
                query = """
                    SELECT DISTINCT grade_technical 
                    FROM trades 
                    WHERE account_id = ? AND status = 'CLOSED' 
                    AND grade_technical IS NOT NULL 
                    AND grade_technical != 'N/A'
                    ORDER BY grade_technical
                """
                cursor.execute(query, (account_id,))
            else:
                return []
            
            results = cursor.fetchall()
            return [row[0] for row in results if row[0]]
            
    except Exception as e:
        logger.error(f"Failed to get unique filter values: {e}")
        return []

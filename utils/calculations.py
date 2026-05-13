"""
Trading calculation functions
All trade-related mathematical calculations
"""

from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def calculate_position_size(account_equity: float, risk_percentage: float,
                           entry_price: float, stop_loss: float,
                           direction: str) -> float:
    """
    Calculate position size based on risk parameters
    
    Formula:
        risk_amount = account_equity * (risk_percentage / 100)
        risk_per_unit = abs(entry_price - stop_loss)
        position_size = risk_amount / risk_per_unit
    
    Args:
        account_equity: Account equity amount
        risk_percentage: Risk percentage (e.g., 1 for 1%)
        entry_price: Entry price
        stop_loss: Stop loss price
        direction: 'LONG' or 'SHORT'
        
    Returns:
        Position size (number of units/contracts)
    """
    if account_equity <= 0 or risk_percentage <= 0 or entry_price <= 0 or stop_loss <= 0:
        logger.warning("Invalid input for position size calculation")
        return 0
    
    risk_amount = account_equity * (risk_percentage / 100)
    risk_per_unit = abs(entry_price - stop_loss)
    
    if risk_per_unit == 0:
        logger.warning("Risk per unit is zero - cannot calculate position size")
        return 0
    
    position_size = risk_amount / risk_per_unit
    
    logger.debug(f"Position size calculated: {position_size:.4f} units")
    return round(position_size, 4)


def calculate_risk_amount(account_equity: float, risk_percentage: float) -> float:
    """
    Calculate risk amount in currency
    
    Args:
        account_equity: Account equity
        risk_percentage: Risk percentage
        
    Returns:
        Risk amount in currency
    """
    return account_equity * (risk_percentage / 100)


def calculate_prospective_r(entry_price: float, target: float,
                           stop_loss: float, direction: str) -> float:
    """
    Calculate prospective R-multiple
    
    Formula:
        For LONG: R = (target - entry) / (entry - stop)
        For SHORT: R = (entry - target) / (stop - entry)
    
    Args:
        entry_price: Entry price
        target: Target price
        stop_loss: Stop loss price
        direction: 'LONG' or 'SHORT'
        
    Returns:
        Prospective R-multiple
    """
    if entry_price <= 0 or target <= 0 or stop_loss <= 0:
        return 0
    
    if direction == 'LONG':
        reward = target - entry_price
        risk = entry_price - stop_loss
    else:  # SHORT
        reward = entry_price - target
        risk = stop_loss - entry_price
    
    if risk == 0:
        return 0
    
    r_multiple = reward / risk
    return round(r_multiple, 2)


def calculate_pnl(entry_price: float, exit_price: float,
                 position_size: float, direction: str) -> float:
    """
    Calculate profit/loss
    
    Args:
        entry_price: Entry price
        exit_price: Exit price
        position_size: Position size
        direction: 'LONG' or 'SHORT'
        
    Returns:
        P&L amount
    """
    if direction == 'LONG':
        pnl = (exit_price - entry_price) * position_size
    else:  # SHORT
        pnl = (entry_price - exit_price) * position_size
    
    return round(pnl, 2)


def calculate_total_r(
    entry_price: float,
    exit_price: float,
    stop_loss: float,
    direction: str,
    pnl: float = None,
    risk_amount: float = None
) -> float:
    """
    Calculate realized R-multiple for a closed trade.

    Uses dollar-based R (PnL / Risk_Amount) which is always accurate.
    Falls back to price-based only if dollar values are unavailable.

    Args:
        entry_price:  Weighted average entry price
        exit_price:   Weighted average exit price
        stop_loss:    Stop loss price
        direction:    'LONG' or 'SHORT'
        pnl:          Realized P&L in dollars (preferred path)
        risk_amount:  Dollar risk amount at trade open (preferred path)

    Returns:
        R-multiple as float
    """
    try:
        # PRIMARY: dollar-based — always accurate, immune to tight stops
        if pnl is not None and risk_amount is not None and risk_amount > 0:
            return round(pnl / risk_amount, 4)

        # FALLBACK: price-based (only used if risk_amount unavailable)
        sl_distance = abs(entry_price - stop_loss)
        if sl_distance <= 0:
            return 0.0

        if direction == 'LONG':
            r = (exit_price - entry_price) / sl_distance
        else:
            r = (entry_price - exit_price) / sl_distance

        return round(r, 4)

    except (TypeError, ZeroDivisionError):
        return 0.0

def calculate_roe_percentage(pnl: float, risk_amount: float) -> float:
    """
    Calculate Return on Equity percentage
    
    Args:
        pnl: Profit/Loss amount
        risk_amount: Risk amount
        
    Returns:
        ROE percentage
    """
    if risk_amount == 0:
        return 0
    
    roe = (pnl / risk_amount) * 100
    return round(roe, 2)


def calculate_trade_duration(entry_datetime: datetime, exit_datetime: datetime) -> int:
    """
    Calculate trade duration in minutes
    
    Args:
        entry_datetime: Entry datetime
        exit_datetime: Exit datetime
        
    Returns:
        Duration in minutes
    """
    if not entry_datetime or not exit_datetime:
        return 0
    
    duration = exit_datetime - entry_datetime
    return int(duration.total_seconds() / 60)


def format_duration(minutes: int) -> str:
    """
    Format duration for display
    
    Args:
        minutes: Duration in minutes
        
    Returns:
        Formatted duration string
    """
    if minutes < 60:
        return f"{minutes}m"
    elif minutes < 1440:  # Less than a day
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"
    else:
        days = minutes // 1440
        hours = (minutes % 1440) // 60
        return f"{days}d {hours}h"


def calculate_average_entry(entries: list) -> float:
    """
    Calculate average entry price for multiple entries
    
    Args:
        entries: List of tuples (price, size)
        
    Returns:
        Weighted average entry price
    """
    if not entries:
        return 0
    
    total_value = sum(price * size for price, size in entries)
    total_size = sum(size for _, size in entries)
    
    if total_size == 0:
        return 0
    
    return round(total_value / total_size, 4)


def calculate_average_exit(exits: list) -> float:
    """
    Calculate average exit price for multiple exits
    
    Args:
        exits: List of tuples (price, size)
        
    Returns:
        Weighted average exit price
    """
    return calculate_average_entry(exits)


def calculate_mae_mfe(direction: str, entry_price: float, 
                     high_price: float, low_price: float) -> tuple:
    """
    Calculate Maximum Adverse Excursion and Maximum Favorable Excursion
    
    Args:
        direction: 'LONG' or 'SHORT'
        entry_price: Entry price
        high_price: Highest price during trade
        low_price: Lowest price during trade
        
    Returns:
        Tuple of (MAE, MFE) in points
    """
    if direction == 'LONG':
        mae = entry_price - low_price
        mfe = high_price - entry_price
    else:  # SHORT
        mae = high_price - entry_price
        mfe = entry_price - low_price
    
    return round(mae, 4), round(mfe, 4)


def is_within_risk_limit(risk_percentage: float, max_risk: float = 2.0) -> bool:
    """
    Check if risk is within acceptable limits
    
    Args:
        risk_percentage: Risk percentage
        max_risk: Maximum allowed risk percentage (default 2%)
        
    Returns:
        True if within limit, False otherwise
    """
    return risk_percentage <= max_risk

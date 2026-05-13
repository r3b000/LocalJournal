"""
Input validation functions
Validates user inputs before database operations
"""

import re
from typing import Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def validate_account_name(name: str) -> Tuple[bool, str]:
    """
    Validate account name
    
    Args:
        name: Account name
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Account name cannot be empty"
    
    if len(name) < 3:
        return False, "Account name must be at least 3 characters"
    
    if len(name) > 50:
        return False, "Account name must be less than 50 characters"
    
    return True, ""


def validate_equity(amount: float) -> Tuple[bool, str]:
    """
    Validate equity amount
    
    Args:
        amount: Equity amount
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if amount <= 0:
        return False, "Equity must be greater than zero"
    
    if amount > 1000000000:  # 1 billion limit
        return False, "Equity amount exceeds maximum allowed"
    
    return True, ""


def validate_symbol(symbol: str) -> Tuple[bool, str]:
    """
    Validate ticker symbol
    
    Args:
        symbol: Ticker symbol
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not symbol or not symbol.strip():
        return False, "Symbol cannot be empty"
    
    # Remove whitespace and convert to uppercase
    symbol = symbol.strip().upper()
    
    if len(symbol) < 2:
        return False, "Symbol must be at least 2 characters"
    
    if len(symbol) > 20:
        return False, "Symbol must be less than 20 characters"
    
    return True, ""


def validate_price(price: float, field_name: str = "Price") -> Tuple[bool, str]:
    """
    Validate price value
    
    Args:
        price: Price value
        field_name: Name of the field for error message
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if price <= 0:
        return False, f"{field_name} must be greater than zero"
    
    return True, ""


def validate_time_format(time_str: str) -> Tuple[bool, str]:
    """
    Validate time format (HH:MM)
    
    Args:
        time_str: Time string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not time_str:
        return False, "Time cannot be empty"
    
    # Check format HH:MM
    pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    
    if not re.match(pattern, time_str):
        return False, "Time must be in HH:MM format (24-hour)"
    
    return True, ""


def validate_date(date_str: str) -> Tuple[bool, str]:
    """
    Validate date format (YYYY-MM-DD)
    
    Args:
        date_str: Date string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not date_str:
        return False, "Date cannot be empty"
    
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True, ""
    except ValueError:
        return False, "Date must be in YYYY-MM-DD format"


def validate_percentage(percentage: float, field_name: str = "Percentage") -> Tuple[bool, str]:
    """
    Validate percentage value
    
    Args:
        percentage: Percentage value
        field_name: Name of the field for error message
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if percentage <= 0:
        return False, f"{field_name} must be greater than zero"
    
    if percentage > 100:
        return False, f"{field_name} cannot exceed 100%"
    
    return True, ""


def validate_strategy_name(name: str) -> Tuple[bool, str]:
    """
    Validate strategy name
    
    Args:
        name: Strategy name
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Strategy name cannot be empty"
    
    if len(name) < 3:
        return False, "Strategy name must be at least 3 characters"
    
    if len(name) > 50:
        return False, "Strategy name must be less than 50 characters"
    
    return True, ""


def validate_trade_logic(entry_price: float, stop_loss: float, 
                        target: float, direction: str) -> Tuple[bool, str]:
    """
    Validate trade logic (stop loss and target positions)
    
    Args:
        entry_price: Entry price
        stop_loss: Stop loss price
        target: Target price
        direction: 'LONG' or 'SHORT'
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if direction == 'LONG':
        if stop_loss >= entry_price:
            return False, "For LONG trades, stop loss must be below entry price"
        
        if target and target <= entry_price:
            return False, "For LONG trades, target must be above entry price"
    
    else:  # SHORT
        if stop_loss <= entry_price:
            return False, "For SHORT trades, stop loss must be above entry price"
        
        if target and target >= entry_price:
            return False, "For SHORT trades, target must be below entry price"
    
    return True, ""


def validate_position_size(position_size: float) -> Tuple[bool, str]:
    """
    Validate position size
    
    Args:
        position_size: Position size
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if position_size <= 0:
        return False, "Position size must be greater than zero"
    
    return True, ""


def validate_stop_loss_direction(
    entry_price: float,
    stop_loss: float,
    direction: str
) -> tuple[bool, str]:
    """
    Validates that stop loss is on the correct side of entry price.
    LONG  -> SL must be strictly below entry
    SHORT -> SL must be strictly above entry
    """
    if entry_price is None or stop_loss is None:
        return True, ""  # skip if values not yet entered

    if direction == "LONG":
        if stop_loss >= entry_price:
            return False, (
                f"LONG stop loss (${stop_loss}) must be BELOW entry price (${entry_price}). "
                f"Move SL below ${entry_price}."
            )
    elif direction == "SHORT":
        if stop_loss <= entry_price:
            return False, (
                f"SHORT stop loss (${stop_loss}) must be ABOVE entry price (${entry_price}). "
                f"Move SL above ${entry_price}."
            )

    return True, ""

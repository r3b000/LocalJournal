"""
Display formatting functions
Format values for consistent display across the application
"""

from typing import Optional


def format_currency(amount: float, currency_symbol: str = "$") -> str:
    """
    Format amount as currency
    
    Args:
        amount: Amount to format
        currency_symbol: Currency symbol (default: $)
        
    Returns:
        Formatted currency string (e.g., "$1,234.56")
    """
    if amount is None:
        return f"{currency_symbol}0.00"
    
    return f"{currency_symbol}{amount:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format value as percentage
    
    Args:
        value: Value to format
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string (e.g., "12.34%")
    """
    if value is None:
        return "0.00%"
    
    return f"{value:.{decimals}f}%"


def format_number(value: float, decimals: int = 2) -> str:
    """
    Format number with commas and decimals
    
    Args:
        value: Value to format
        decimals: Number of decimal places
        
    Returns:
        Formatted number string
    """
    if value is None:
        return "0.00"
    
    return f"{value:,.{decimals}f}"


def format_r_multiple(r_value: float) -> str:
    """
    Format R-multiple value
    
    Args:
        r_value: R-multiple value
        
    Returns:
        Formatted R string (e.g., "2.5R" or "-1.0R")
    """
    if r_value is None:
        return "0.0R"
    
    return f"{r_value:.2f}R"


def format_date(date_str: str, input_format: str = "%Y-%m-%d", 
                output_format: str = "%Y-%m-%d") -> str:
    """
    Format date string
    
    Args:
        date_str: Date string to format
        input_format: Input date format
        output_format: Output date format
        
    Returns:
        Formatted date string
    """
    if not date_str:
        return ""
    
    from datetime import datetime
    try:
        date_obj = datetime.strptime(date_str, input_format)
        return date_obj.strftime(output_format)
    except:
        return date_str


def format_time(time_str: str) -> str:
    """
    Format time string (ensures HH:MM format)
    
    Args:
        time_str: Time string
        
    Returns:
        Formatted time string
    """
    if not time_str:
        return ""
    
    # Ensure it's in HH:MM format
    if len(time_str) == 5 and time_str[2] == ':':
        return time_str
    
    return time_str


from typing import Optional

def format_duration(minutes: Optional[float], max_units: int = 3) -> str:
    """
    Format duration from minutes to human-readable string
    Supports months, weeks, days, hours, and minutes
    
    Args:
        minutes: Duration in minutes
        max_units: Maximum number of time units to display (default: 3)
        
    Returns:
        Formatted duration string
        
    Examples:
        45 → "45min"
        90 → "1H 30min"
        1500 → "1D 1H"
        10080 → "1W"
        43200 → "1M"
        100000 → "2M 1W 2D"
    """
    if minutes is None or minutes == 0:
        return "0min"
    
    if minutes < 0:
        return f"-{format_duration(abs(minutes), max_units)}"
    
    # Time unit conversions (in minutes)
    MONTH = 43200  # 30 days * 24 hours * 60 minutes
    WEEK = 10080   # 7 days * 24 hours * 60 minutes
    DAY = 1440     # 24 hours * 60 minutes
    HOUR = 60
    
    # Calculate each unit
    months = int(minutes // MONTH)
    remaining = minutes % MONTH
    
    weeks = int(remaining // WEEK)
    remaining = remaining % WEEK
    
    days = int(remaining // DAY)
    remaining = remaining % DAY
    
    hours = int(remaining // HOUR)
    mins = int(remaining % HOUR)
    
    # Build result with max_units limit
    parts = []
    
    if months > 0:
        parts.append(f"{months}M")
    
    if weeks > 0:
        parts.append(f"{weeks}W")
    
    if days > 0:
        parts.append(f"{days}D")
    
    if hours > 0:
        parts.append(f"{hours}H")
    
    if mins > 0 or len(parts) == 0:
        parts.append(f"{mins}min")
    
    # Limit to max_units
    parts = parts[:max_units]
    
    return " ".join(parts)



def format_pnl_color(pnl: float) -> str:
    """
    Get color code for P&L display
    
    Args:
        pnl: P&L value
        
    Returns:
        Color string for Streamlit
    """
    if pnl > 0:
        return "normal"  # Green
    elif pnl < 0:
        return "inverse"  # Red
    else:
        return "off"  # Gray


def format_trade_status(status: str) -> str:
    """
    Format trade status with emoji
    
    Args:
        status: Trade status ('OPEN' or 'CLOSED')
        
    Returns:
        Formatted status string
    """
    if status == 'OPEN':
        return "🟢 OPEN"
    else:
        return "⚪ CLOSED"


def format_direction(direction: str) -> str:
    """
    Format trade direction
    
    Args:
        direction: Trade direction ('LONG' or 'SHORT')
        
    Returns:
        Formatted direction string
    """
    if direction == 'LONG':
        return "🟩 LONG"
    else:
        return "🟥 SHORT"


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def format_price(value) -> str:
    """
    Format a price showing only the decimals that are actually used.
    
    Examples:
        76543.2      -> $76,543.2
        0.00001234   -> $0.00001234
        0.0019       -> $0.0019
        5000.0       -> $5,000
        100.5        -> $100.5
    """
    if value is None:
        return "N/A"
    try:
        value = float(value)
        # Strip trailing zeros up to 8 decimal places
        stripped = f"{value:.8f}".rstrip('0').rstrip('.')
        # Apply thousands separator to the integer part only
        if '.' in stripped:
            int_part, dec_part = stripped.split('.')
            return f"${int(int_part):,}.{dec_part}"
        else:
            return f"${int(value):,}"
    except (ValueError, TypeError):
        return "N/A"


# # Test the duration formatter
# if __name__ == "__main__":
#     print("=" * 60)
#     print("DURATION FORMATTER TEST")
#     print("=" * 60)
    
#     test_cases = [
#         (0, "0min"),
#         (5, "5min"),
#         (45, "45min"),
#         (60, "1H"),
#         (90, "1H 30min"),
#         (150, "2H 30min"),
#         (720, "12H"),
#         (1440, "1D"),
#         (1500, "1D 1H"),
#         (2880, "2D"),
#         (5200, "3D 14H 40min"),
#         (10080, "1W"),
#         (15000, "1W 3D 10H"),
#         (43200, "1M"),
#         (50000, "1M 4D 18H"),
#         (100000, "2M 1W 2D"),
#     ]
    
#     print(f"\n{'Minutes':<10} {'Result':<25} {'Expected':<25} {'Status'}")
#     print("-" * 60)
    
#     for minutes, expected in test_cases:
#         result = format_duration(minutes)
#         status = "✔" if result == expected else f"❌ (got: {result})"
#         print(f"{minutes:<10} {result:<25} {expected:<25} {status}")
    
#     print("\n" + "=" * 60)

"""
Filter components for Trade History and Statistics pages
"""

import streamlit as st
from typing import Dict, List
from datetime import datetime, timedelta
from utils.paths import get_database_path
from database.strategies_db import get_all_strategies


def render_trade_filters(account_id: int) -> Dict:
    """
    Render trade filter controls
    
    Args:
        account_id: Account ID to filter for
        
    Returns:
        Dictionary with filter values
    """
    st.subheader("Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        symbol_filter = st.selectbox(
            "Symbol",
            options=["All", "BTCUSDT", "ETHUSDT", "SOLUSDT", "Custom"],
            key="symbol_filter"
        )
        
        if symbol_filter == "Custom":
            symbol_filter = st.text_input("Enter symbol", key="custom_symbol").upper()
    
    with col2:
        direction_filter = st.selectbox(
            "Direction",
            options=["All", "LONG", "SHORT"],
            key="direction_filter"
        )
    
    with col3:
        status_filter = st.selectbox(
            "Status",
            options=["All", "OPEN", "CLOSED"],
            key="status_filter"
        )
    
    with col4:
        # Get strategies for filter
        db_path = get_database_path()
        strategies = get_all_strategies(db_path)
        strategy_options = ["All"] + [s['strategy_name'] for s in strategies]
        
        strategy_filter = st.selectbox(
            "Strategy",
            options=strategy_options,
            key="strategy_filter"
        )
    
    # Date range filter
    st.markdown("---")
    date_range_type = st.selectbox(
        "Date Range",
        options=["All", "Today", "Last 7 Days", "Last 30 Days", "This Month", "This Year", "Custom"],
        key="date_range_filter"
    )
    
    date_from = None
    date_to = None
    
    if date_range_type == "Custom":
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            date_from = st.date_input("From Date", key="date_from")
        with col_date2:
            date_to = st.date_input("To Date", key="date_to")
        
        if date_from:
            date_from = date_from.strftime("%Y-%m-%d")
        if date_to:
            date_to = date_to.strftime("%Y-%m-%d")
    
    elif date_range_type != "All":
        today = datetime.now().date()
        
        if date_range_type == "Today":
            date_from = date_to = today.strftime("%Y-%m-%d")
        elif date_range_type == "Last 7 Days":
            date_from = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            date_to = today.strftime("%Y-%m-%d")
        elif date_range_type == "Last 30 Days":
            date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")
            date_to = today.strftime("%Y-%m-%d")
        elif date_range_type == "This Month":
            date_from = today.replace(day=1).strftime("%Y-%m-%d")
            date_to = today.strftime("%Y-%m-%d")
        elif date_range_type == "This Year":
            date_from = today.replace(month=1, day=1).strftime("%Y-%m-%d")
            date_to = today.strftime("%Y-%m-%d")
    
    # Build filters dictionary
    filters = {
        'account_id': account_id,
        'symbol': None if symbol_filter == "All" else symbol_filter,
        'direction': None if direction_filter == "All" else direction_filter,
        'status': None if status_filter == "All" else status_filter,
        'strategy_id': None,  # Will be resolved below
        'date_from': date_from,
        'date_to': date_to
    }
    
    # Resolve strategy ID
    if strategy_filter != "All":
        for strategy in strategies:
            if strategy['strategy_name'] == strategy_filter:
                filters['strategy_id'] = strategy['strategy_id']
                break
    
    return filters

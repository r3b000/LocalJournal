"""
Account selector component
Reusable component for account selection across pages
"""

import streamlit as st
from typing import Optional, Dict
from utils.paths import get_database_path
from database.accounts_db import get_all_accounts
from utils.session_state import set_selected_account, get_selected_account


def render_account_selector(label: str = "Select Account", 
                           show_balance: bool = True) -> Optional[Dict]:
    """
    Render account selector dropdown
    
    Args:
        label: Label for the selector
        show_balance: Whether to show balance in dropdown
        
    Returns:
        Selected account dictionary or None
    """
    db_path = get_database_path()
    accounts = get_all_accounts(db_path)
    
    if not accounts:
        st.warning("No accounts found. Please create an account first in the Accounts page.")
        return None
    
    # Create options for dropdown
    if show_balance:
        account_options = {
            f"{acc['account_name']} (${acc['current_equity']:,.2f})": acc['account_id']
            for acc in accounts
        }
    else:
        account_options = {
            acc['account_name']: acc['account_id']
            for acc in accounts
        }
    
    # Get currently selected account
    current_account_id = get_selected_account()
    
    # Find default index
    default_index = 0
    if current_account_id:
        for idx, acc_id in enumerate(account_options.values()):
            if acc_id == current_account_id:
                default_index = idx
                break
    
    # Render selector
    selected_option = st.selectbox(
        label,
        options=list(account_options.keys()),
        index=default_index
    )
    
    if selected_option:
        selected_account_id = account_options[selected_option]
        set_selected_account(selected_account_id)
        
        # Return full account data
        for acc in accounts:
            if acc['account_id'] == selected_account_id:
                return acc
    
    return None

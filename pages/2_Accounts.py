"""
Accounts Page
Create and manage trading accounts
"""


import streamlit as st
from utils.paths import get_database_path
from database.accounts_db import (
    create_account,
    get_all_accounts,
    delete_account,
    get_account_stats
)
from utils.validators import validate_account_name, validate_equity
from utils.formatters import format_currency, format_percentage
from utils.png_icons import *

st.set_page_config(page_title="Accounts", page_icon="💼", layout="wide")


icon_header("icons/accounts.png", "Trading Accounts", level="h1")
st.markdown("Manage your trading accounts")
st.markdown("---")


db_path = get_database_path()



#  ICONS

danger_icon = get_png_icon("icons/danger.png", 42, 42)


# Create Account Section
icon_header("icons/add.png", "Create New Account", level="h3")


with st.form("create_account_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        account_name = st.text_input("Account Name*", placeholder="e.g., Demo Account")
    
    with col2:
        starting_equity = st.number_input("Starting Equity*", min_value=0.0, value=10000.0, step=100.0)
    
    strategy_description = st.text_area(
        "Account Description (Optional)",
        placeholder="Describe your usage for this account..."
    )
    
    submitted = st.form_submit_button("Create Account", type="primary")
    
    if submitted:
        # Validate inputs
        valid_name, name_error = validate_account_name(account_name)
        valid_equity, equity_error = validate_equity(starting_equity)
        
        if not valid_name:
            st.error(f"Invalid account name: {name_error}")
        elif not valid_equity:
            st.error(f"Invalid equity: {equity_error}")
        else:
            # Create account
            account_id = create_account(db_path, account_name, starting_equity, strategy_description)
            
            if account_id:
                st.success(f"Account '{account_name}' created successfully!")
                from utils.cache_manager import clear_cache_after_account_operation
                clear_cache_after_account_operation()
                st.rerun()
            else:
                st.error("Failed to create account. Account name might already exist.")


st.markdown("---")


# View Accounts Section

icon_header("icons/list.png", "Your Accounts", level="h3")

accounts = get_all_accounts(db_path)


if accounts:
    for account in accounts:
        with st.expander(f"**{account['account_name']}** - {format_currency(account['current_equity'])}", expanded=False):
            
            # Get account statistics
            stats = get_account_stats(db_path, account['account_id'])
            
            col_acc1, col_acc2 = st.columns(2)
            
            with col_acc1:
                st.markdown("**Account Details**")
                st.write(f"**Account ID:** {account['account_id']}")
                st.write(f"**Account Name:** {account['account_name']}")
                st.write(f"**Starting Equity:** {format_currency(account['starting_equity'])}")
                st.write(f"**Current Equity:** {format_currency(account['current_equity'])}")
                st.write(f"**Created:** {account['created_at']}")
            
            with col_acc2:
                st.markdown("**Performance**")
                st.write(f"**Total P&L:** {format_currency(stats['total_pnl'])}")
                st.write(f"**ROI:** {format_percentage(stats['roi'])}")
                st.write(f"**Total Trades:** {stats['total_trades']}")
                st.write(f"**Open Trades:** {stats['open_trades']}")
                st.write(f"**Closed Trades:** {stats['closed_trades']}")
            
            if account['strategy_description']:
                st.markdown("**Strategy Description**")
                st.info(account['strategy_description'])
            
            # Danger Zone - Delete Account
            st.markdown("---")
            icon_header("icons/danger.png", "Danger Zone", level="h3")
            
            # Show warning about consequences
            if stats['total_trades'] > 0:
                st.warning(f"This account has **{stats['total_trades']} trade(s)**. Deleting will permanently remove all trades and data!")
            else:
                icon_header("icons/info.png", "This account has no trades. Safe to delete.", level="h3")
            col_delete1, col_delete2, col_delete3 = st.columns([2, 1, 2])
            
            with col_delete2:
                # Checkbox to confirm deletion intent
                delete_confirm = st.checkbox(
                    "I want to delete this account",
                    key=f"confirm_delete_{account['account_id']}",
                    help="Check this box to enable the delete button"
                )
                
                # Delete button (only enabled if checkbox is checked)
                if st.button(
                    "Delete Account",
                    type="secondary",
                    use_container_width=True,
                    disabled=not delete_confirm,
                    key=f"delete_btn_{account['account_id']}"
                ):
                    # Perform deletion
                    success = delete_account(db_path, account['account_id'])
                    
                    if success:
                        st.success(f"Account '{account['account_name']}' deleted successfully!")
                        from utils.cache_manager import clear_cache_after_account_operation
                        clear_cache_after_account_operation()
                        
                        # Clear session state
                        if f"confirm_delete_{account['account_id']}" in st.session_state:
                            del st.session_state[f"confirm_delete_{account['account_id']}"]
                        
                        st.rerun()
                    else:
                        st.error(f"Failed to delete account '{account['account_name']}'")

else:
    st.info("No accounts found. Create your first account above!")


st.markdown("---")
st.caption("💡 Tip: Create separate accounts for different trading styles, brokers, or demo/live trading.")

"""
Session state management for Streamlit
Initializes and manages session state variables
"""

import streamlit as st
from typing import Any


def initialize_session_state():
    """
    Initialize all session state variables with default values
    Should be called once at app startup
    """
    
    # Selected account
    if 'selected_account_id' not in st.session_state:
        st.session_state.selected_account_id = None
    
    # Current page
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"
    
    # Trade form data (for Log Trade page)
    if 'trade_form_data' not in st.session_state:
        st.session_state.trade_form_data = {}
    
    # Mental development worksheet trigger
    if 'show_worksheet_modal' not in st.session_state:
        st.session_state.show_worksheet_modal = False
    
    if 'worksheet_data' not in st.session_state:
        st.session_state.worksheet_data = {}
    
    # Filters (for Trade History and Statistics)
    if 'trade_filters' not in st.session_state:
        st.session_state.trade_filters = {
            'symbol': 'All',
            'direction': 'All',
            'status': 'All',
            'strategy': 'All',
            'date_range': 'All'
        }
    
    # Notifications/messages
    if 'success_message' not in st.session_state:
        st.session_state.success_message = None
    
    if 'error_message' not in st.session_state:
        st.session_state.error_message = None
    
    # Data refresh flag
    if 'refresh_data' not in st.session_state:
        st.session_state.refresh_data = False


def set_selected_account(account_id: int):
    """Set the currently selected account"""
    st.session_state.selected_account_id = account_id


def get_selected_account() -> int:
    """Get the currently selected account ID"""
    return st.session_state.get('selected_account_id', None)


def set_success_message(message: str):
    """Set a success message to display"""
    st.session_state.success_message = message


def set_error_message(message: str):
    """Set an error message to display"""
    st.session_state.error_message = message


def clear_messages():
    """Clear all messages"""
    st.session_state.success_message = None
    st.session_state.error_message = None


def trigger_worksheet_modal(category: str, issue_type: str, emotion: str, occurrence_count: int):
    """Trigger the mental development worksheet modal"""
    st.session_state.show_worksheet_modal = True
    st.session_state.worksheet_data = {
        'category': category,
        'issue_type': issue_type,
        'emotion': emotion,
        'occurrence_count': occurrence_count
    }


def close_worksheet_modal():
    """Close the worksheet modal"""
    st.session_state.show_worksheet_modal = False
    st.session_state.worksheet_data = {}


def set_value(key: str, value: Any):
    """Set a session state value"""
    st.session_state[key] = value


def get_value(key: str, default: Any = None) -> Any:
    """Get a session state value"""
    return st.session_state.get(key, default)

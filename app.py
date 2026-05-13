"""
LocalJournal - Desktop Trading Journal Application
Main entry point for the application
"""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import utilities
from utils.paths import ensure_app_directories, get_database_path
from utils.session_state import initialize_session_state
from utils.logger import setup_logger
from database.schema import initialize_database
from config.constants import APP_NAME, APP_VERSION, DISCLAIMER_TEXT
from config.settings import app_settings
from utils.paths import get_settings_file
from utils.png_icons import icon_header

# Only configure page if not already configured
try:
    st.set_page_config(
        page_title=f"{APP_NAME}",
        page_icon="𝄜",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except:
    pass  # Already configured in desktop mode

# Setup logger
logger = setup_logger()


def show_disclaimer():
    """Display disclaimer and get user acceptance"""
    st.title("⚠ Important Legal Disclaimer")
    
    st.markdown(DISCLAIMER_TEXT)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("✔ I Accept and Understand", type="primary", use_container_width=True):
            app_settings.accept_disclaimer()
            app_settings.mark_launched()
            st.rerun()
    
    st.markdown("---")
    st.error("You must accept the disclaimer to use this application.")


def main():
    """Main application entry point"""
    
    # Initialize logger
    logger.info("=" * 50)
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    logger.info("=" * 50)
    
    # Ensure directories exist
    ensure_app_directories()
    logger.info("✓ App directories verified")
    
    # Initialize settings
    app_settings.initialize(get_settings_file())
    logger.info("✓ Settings initialized")
    
    # Check disclaimer acceptance
    if not app_settings.is_disclaimer_accepted():
        show_disclaimer()
        return
    
    # Initialize database
    db_path = get_database_path()
    initialize_database(db_path)
    logger.info(f"✓ Database initialized: {db_path}")
    
    # Initialize session state
    initialize_session_state()
    logger.info("✓ Session state initialized")
    
    # Display main page content
    display_welcome_page()


def display_welcome_page():
    """Display the home/welcome page"""


    icon_header("icons/icon.png", "Trading Accounts", level="h1")
    

    st.markdown("#### Your Personal Trading Journal - 100% Local, 100% Private")
    st.markdown("---")
    
    # Feature cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **Dashboard**
        
        View your trading performance at a glance with comprehensive statistics and recent trades.
        """)
    
    with col2:
        st.info("""
        **Log Trade**
        
        Record new trades with detailed entry, risk management, and position sizing calculations.
        """)
    
    with col3:
        st.info("""
        **Statistics**
        
        Analyze your trading performance with advanced analytics and visual reports.
        """)
    
    st.markdown("---")
    
    # Quick start guide
    st.subheader("Quick Start Guide")
    
    with st.expander("First Time Setup", expanded=False):
        st.markdown("""
        ### Getting Started with LocalJournal
        
        **1. Create an Account**
        - Navigate to **Accounts** page in the sidebar
        - Click "Create New Account"
        - Enter your account name and starting equity
        
        **2. Create Strategies**
        - Go to **Strategies** page
        - Define your trading strategies
        - Add descriptions for future reference
        
        **3. Log Your First Trade**
        - Head to **Log Trade** page
        - Fill in trade details, risk management parameters
        - Upload screenshots (optional)
        - Click "LOG TRADE" to save
        
        **4. Monitor Performance**
        - Check **Dashboard** for overview
        - View **Statistics** for detailed analytics
        - Use **Trade History** to review all trades
        
        **5. Track Mental Development**
        - Use **Mental Development** to log trading psychology issues
        - Complete worksheets when patterns emerge (after 5 occurrences)
        - Track your emotional growth as a trader
        
        **6. Manage Your Data**
        - Visit **Data Management** page
        - Create regular backups
        - Export data for safekeeping
        """)
    
    with st.expander("Key Features", expanded=False):
        st.markdown("""
        ### What Makes LocalJournal Powerful
        
        **Complete Privacy**
        - All data stored locally on your Desktop
        - No cloud uploads, no internet required
        - Your trading data stays with you
        
        **Comprehensive Trade Logging**
        - Position sizing calculator
        - Risk management tracking
        - R-multiple calculations
        - Trade grading system
        - Screenshot attachments
        
        **Advanced Analytics**
        - Win rate and profit factor
        - Calendar heatmap
        - Performance by symbol, strategy, direction
        - Equity curve tracking
        - R-multiple distribution
        
        **Mental Development Tools**
        - Track execution, risk, and management issues
        - Automatic worksheet triggers
        - Emotion pattern recognition
        - Actionable improvement plans
        
        **Data Safety**
        - Built-in backup system
        - Export/import functionality
        - Data integrity checks
        """)
    
    with st.expander("Data Storage Location", expanded=False):
        st.markdown("""
        ### Where Your Data is Stored
        
        **Primary Data Folder:** `Desktop/LocalJournalData/`
        - Database file: `localjournal.db`
        - Screenshots: `screenshots/TRADE_XXX/`
        - Worksheets: `issue_tracker_development/`
        - Logs: `logs/localjournal.log`
        - Auto-backups: `backups/`
        
        **Backup Folder:** `Desktop/LocalJournal_Backups/`
        - Manual backups created from Data Management page
        - Separate from main data for safety
        
        **Tip:** Keep backups on external drive or cloud storage for maximum safety!
        """)
    
    st.markdown("---")
    
    # App info
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.metric("Version", APP_VERSION)
    
    with col_info2:
        st.metric("Database", "SQLite (Local)")
    
    with col_info3:
        st.metric("Status", "✔ Ready")
    
    # Sidebar info
    st.sidebar.markdown("---")
    st.sidebar.caption(f"**{APP_NAME}** v{APP_VERSION}")
    st.sidebar.caption("© 2026 LocalJournal")
    st.sidebar.caption("Open Source | Educational Use Only")


if __name__ == "__main__":
    main()

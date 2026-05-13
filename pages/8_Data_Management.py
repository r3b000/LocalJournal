"""
Data Management Page
Import, export, backup, and restore data
"""

import streamlit as st
import shutil
from pathlib import Path
from datetime import datetime
from utils.paths import (
    get_database_path,
    get_app_data_dir,
    get_app_backups_dir,
    get_backups_dir
)
from utils.formatters import format_number
from database.accounts_db import get_all_accounts
from database.trades_db import get_all_trades
from database.strategies_db import get_all_strategies
import os

st.set_page_config(page_title="Data Management", page_icon="💾", layout="wide")

from utils.png_icons import icon_header

icon_header("icons/floppy_disc.png", "Data Management",width=51, height=51, level="h1")

st.markdown("Manage your trading data - import, export, backup, and restore")
st.markdown("---")

db_path = get_database_path()
data_dir = get_app_data_dir()
backups_dir = get_app_backups_dir()

# Current Data Location
icon_header("icons/folder.png", "Current Data Location", level="h3")

col_loc1, col_loc2 = st.columns(2)

with col_loc1:
    st.write(f"**Data Folder:** `{data_dir}`")
    st.write(f"**Database Path:** `{db_path}`")
    
    if st.button("Open Data Folder"):
        try:
            os.startfile(str(data_dir))
        except:
            st.info("Please open the folder manually from your Desktop")

with col_loc2:
    if db_path.exists():
        db_size = db_path.stat().st_size / 1024  # KB
        db_modified = datetime.fromtimestamp(db_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        
        st.success("[ OK ] Database Found!")
        st.write(f"**Size:** {db_size:.2f} KB")
        st.write(f"**Last Modified:** {db_modified}")
    else:
        st.error("[ X ] Database not found!")

st.markdown("---")

# Data Statistics

icon_header("icons/data_stats.png", "Data Statistics", level="h3")

accounts = get_all_accounts(db_path)
trades = get_all_trades(db_path)
strategies = get_all_strategies(db_path)

col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

with col_stat1:
    st.metric("Accounts", len(accounts))

with col_stat2:
    st.metric("Total Trades", len(trades))

with col_stat3:
    st.metric("Strategies", len(strategies))

with col_stat4:
    if db_path.exists():
        st.metric("Database Size", f"{db_path.stat().st_size / 1024:.2f} KB")
    else:
        st.metric("Database Size", "0 KB")

st.markdown("---")

# Import Database

icon_header("icons/import_data.png", "Import Database", level="h3")

st.info("""
**Use this when:**
- Switching to a new computer
- Restoring from backup
- Transferring data between devices
""")

uploaded_db = st.file_uploader(
    "Upload Database File (.db)",
    type=['db'],
    help="Select a LocalJournal database file to import"
)

if uploaded_db:
    st.write(f"**File:** {uploaded_db.name}")
    st.write(f"**Size:** {uploaded_db.size / 1024:.2f} KB")
    
    st.warning("[ ! ] This will replace your current database! A backup will be created automatically.")
    
    confirm_import = st.checkbox("I understand that my current data will be replaced")
    
    if st.button("📥 Import Database", type="primary", disabled=not confirm_import):
        try:
            # Create backup first
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = get_backups_dir() / f"before_import_{timestamp}.db"
            
            if db_path.exists():
                shutil.copy2(db_path, backup_path)
                st.info(f"[ OK ] Backup created: {backup_path.name}")
            
            # Import new database
            with open(db_path, 'wb') as f:
                f.write(uploaded_db.getbuffer())
            
            st.success("[ OK ] Database imported successfully!")
            st.info("Please refresh the page to see your imported data.")
            
        except Exception as e:
            st.error(f"[ X ] Import failed: {e}")

st.markdown("---")

# Export Database
icon_header("icons/export_data.png", "Export Database", level="h3")

st.info("""
**Use this when:**
- Moving to a new computer
- Creating a backup
- Sharing data with another device
""")

if db_path.exists():
    with open(db_path, 'rb') as f:
        db_bytes = f.read()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_filename = f"localjournal_export_{timestamp}.db"
    
    st.download_button(
        label="⤋ Download Database File",
        data=db_bytes,
        file_name=export_filename,
        mime="application/octet-stream",
        help="Download your database to your Downloads folder"
    )
else:
    st.error("[ X ] No database found to export")

st.markdown("---")

# Create Backup
icon_header("icons/backup.png", "Create Backup", level="h3")

st.info("""
**Create a timestamped backup of your current data.**

Backups are saved to: `Desktop/LocalJournal_Backups/`
""")

col_backup1, col_backup2 = st.columns(2)

with col_backup1:
    if st.button("Create Backup Now", type="primary"):
        try:
            # Ensure backup directory exists
            backups_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"localjournal_backup_{timestamp}.db"
            backup_path = backups_dir / backup_filename
            
            # Copy database
            if db_path.exists():
                shutil.copy2(db_path, backup_path)
                
                backup_size = backup_path.stat().st_size / 1024
                
                st.success(f"[ OK ] Backup created successfully!")
                st.info(f"**File:** {backup_filename}")
                st.info(f"**Size:** {backup_size:.2f} KB")
                st.info(f"**Location:** {backups_dir}")
            else:
                st.error("[ X ] No database found to backup")
                
        except Exception as e:
            st.error(f"[ X ] Backup failed: {e}")

with col_backup2:
    st.markdown("**Last Backup Info**")
    
    # Find most recent backup
    if backups_dir.exists():
        backups = sorted(backups_dir.glob("localjournal_backup_*.db"), key=os.path.getmtime, reverse=True)
        
        if backups:
            last_backup = backups[0]
            last_backup_time = datetime.fromtimestamp(last_backup.stat().st_mtime)
            last_backup_size = last_backup.stat().st_size / 1024
            
            st.write(f"**Date:** {last_backup_time.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"**Size:** {last_backup_size:.2f} KB")
            st.write(f"**File:** {last_backup.name}")
        else:
            st.info("No backups found")
    else:
        st.info("No backups folder found")

st.markdown("---")

# Restore from Backup
icon_header("icons/restore_backup.png", "Restore from Backup", level="h3")

st.info("""
**Restore your data from a previous backup.**

[ ! ] Warning: This will replace your current data!
""")

uploaded_backup = st.file_uploader(
    "Select Backup File to Restore (.db)",
    type=['db'],
    key="restore_upload",
    help="Select a backup database file to restore"
)

if uploaded_backup:
    st.write(f"**File:** {uploaded_backup.name}")
    st.write(f"**Size:** {uploaded_backup.size / 1024:.2f} KB")
    
    st.warning("[ ! ] This will replace your current data! A safety backup will be created first.")
    
    confirm_restore = st.checkbox("I understand that my current data will be replaced", key="confirm_restore")
    
    if st.button("♻️ Restore Backup", type="primary", disabled=not confirm_restore):
        try:
            # Create safety backup first
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safety_backup_path = get_backups_dir() / f"before_restore_{timestamp}.db"
            
            if db_path.exists():
                shutil.copy2(db_path, safety_backup_path)
                st.info(f"[ OK ] Safety backup created: {safety_backup_path.name}")
            
            # Restore from backup
            with open(db_path, 'wb') as f:
                f.write(uploaded_backup.getbuffer())
            
            st.success("[ OK ] Database restored successfully!")
            st.info("Please refresh the page to see your restored data.")
            
        except Exception as e:
            st.error(f"[ X ] Restore failed: {e}")

st.markdown("---")

# Available Backups List
icon_header("icons/available_database.png", "Available Backups", level="h3")


if backups_dir.exists():
    # Get all backups
    all_backups = sorted(backups_dir.glob("*.db"), key=os.path.getmtime, reverse=True)
    
    if all_backups:
        st.write(f"**Found {len(all_backups)} backup(s) in:** `{backups_dir}`")
        
        for backup_file in all_backups[:10]:  # Show last 10 backups
            backup_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            backup_size = backup_file.stat().st_size / 1024
            
            col_b1, col_b2, col_b3 = st.columns([3, 2, 1])
            
            with col_b1:
                st.write(f"🗎 **{backup_file.name}**")
            
            with col_b2:
                st.write(f"{backup_time.strftime('%Y-%m-%d %H:%M')} | {backup_size:.2f} KB")
            
            with col_b3:
                with open(backup_file, 'rb') as f:
                    st.download_button(
                        label="⤋",
                        data=f.read(),
                        file_name=backup_file.name,
                        key=f"download_{backup_file.name}"
                    )
            
            st.markdown("---")
        
        if len(all_backups) > 10:
            st.info(f"Showing 10 most recent backups. {len(all_backups) - 10} more available in folder.")
    else:
        st.info("No backup files found in backup folder.")
else:
    st.info("Backup folder not found. Create your first backup above!")

st.markdown("---")

# Data Management Tips
icon_header("icons/yellow_lamp.png", "Data Management Tips", level="h3")

col_tip1, col_tip2 = st.columns(2)

with col_tip1:
    st.markdown("""
    **Backup Recommendations:**
    - Backup weekly or after significant trading sessions
    - Keep multiple backup copies
    - Store backups in different locations
    - Test restore functionality occasionally
    """)

with col_tip2:
    st.markdown("""
    **Storage Locations:**
    - External USB drive
    - Cloud storage (Dropbox, Google Drive)
    - Email to yourself
    - Secondary computer
    - Encrypted folder
    """)

st.markdown("---")
st.success("[ OK ] Your data is portable! Just take the `localjournal.db` file to any device and import it.")
st.caption("💡 Pro Tip: Keep a backup on your phone via cloud sync for easy access anywhere!")

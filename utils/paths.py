"""
Path management for the application
Handles all file system paths for data storage
"""

from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def get_desktop_path() -> Path:
    """Get user's desktop path (cross-platform)"""
    return Path.home() / "Desktop"


def get_app_data_dir() -> Path:
    """Get main application data directory"""
    return get_desktop_path() / "LocalJournalData"


def get_app_backups_dir() -> Path:
    """Get application backups directory (separate from data)"""
    return get_desktop_path() / "LocalJournal_Backups"


def get_database_path() -> Path:
    """Get database file path"""
    return get_app_data_dir() / "localjournal.db"


def get_screenshots_dir() -> Path:
    """Get screenshots root directory"""
    return get_app_data_dir() / "screenshots"


def get_trade_screenshot_dir(trade_id: int) -> Path:
    """
    Get screenshot directory for a specific trade
    
    Args:
        trade_id: Trade ID
        
    Returns:
        Path to trade screenshot directory
    """
    screenshot_dir = get_screenshots_dir() / f"trade_{trade_id}"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    return screenshot_dir


def get_logs_dir() -> Path:
    """Get logs directory"""
    return get_app_data_dir() / "logs"


def get_backups_dir() -> Path:
    """Get backups directory (inside app data for auto-backups)"""
    return get_app_data_dir() / "backups"


def get_issue_tracker_dir() -> Path:
    """Get mental development issue tracker directory"""
    return get_app_data_dir() / "issue_tracker_development"


def get_settings_file() -> Path:
    """Get settings file path"""
    return get_app_data_dir() / "settings.json"


def ensure_app_directories() -> bool:
    """
    Create all necessary directories if they don't exist
    
    Returns:
        bool: True if successful, False otherwise
    """
    directories = [
        get_app_data_dir(),
        get_app_backups_dir(),
        get_screenshots_dir(),
        get_logs_dir(),
        get_backups_dir(),
        get_issue_tracker_dir()
    ]
    
    try:
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory verified: {directory}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        return False


def get_app_version_file() -> Path:
    """Get version file path"""
    return get_app_data_dir() / "VERSION.txt"


def get_log_file() -> Path:
    """Get main log file path"""
    return get_logs_dir() / "localjournal.log"

# utils/paths.py
# Path management for the application
# Handles all file system paths for data storage — Universal (Windows/macOS/Linux)

import os
import sys
import platform
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_desktop_path() -> Path:
    """
    Get user's Desktop path universally.
    Handles: Windows + OneDrive, Windows standard, macOS, Linux.
    """
    system = platform.system()

    if system == "Windows":
        # Method 1: Windows Registry (handles OneDrive Desktop)
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            desktop, _ = winreg.QueryValueEx(key, "Desktop")
            winreg.CloseKey(key)
            desktop_path = Path(desktop)
            if desktop_path.exists():
                return desktop_path
        except Exception:
            pass

        # Method 2: OneDrive Desktop
        onedrive_desktop = Path.home() / "OneDrive" / "Desktop"
        if onedrive_desktop.exists():
            return onedrive_desktop

        # Method 3: Standard Desktop
        standard = Path.home() / "Desktop"
        standard.mkdir(parents=True, exist_ok=True)
        return standard

    elif system == "Darwin":  # macOS
        desktop = Path.home() / "Desktop"
        desktop.mkdir(parents=True, exist_ok=True)
        return desktop

    else:  # Linux
        try:
            xdg = subprocess.check_output(
                ["xdg-user-dir", "DESKTOP"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            xdg_path = Path(xdg)
            if xdg_path.exists():
                return xdg_path
        except Exception:
            pass

        desktop = Path.home() / "Desktop"
        desktop.mkdir(parents=True, exist_ok=True)
        return desktop


def get_app_data_dir() -> Path:
    return get_desktop_path() / "LocalJournalData"

def get_app_backups_dir() -> Path:
    return get_desktop_path() / "LocalJournalBackups"

def get_database_path() -> Path:
    return get_app_data_dir() / "localjournal.db"

def get_screenshots_dir() -> Path:
    return get_app_data_dir() / "screenshots"

def get_trade_screenshot_dir(trade_id: int) -> Path:
    screenshot_dir = get_screenshots_dir() / f"trade{trade_id}"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    return screenshot_dir

def get_logs_dir() -> Path:
    return get_app_data_dir() / "logs"

def get_backups_dir() -> Path:
    return get_app_data_dir() / "backups"

def get_issue_tracker_dir() -> Path:
    return get_app_data_dir() / "issuetracker_development"

def get_settings_file() -> Path:
    return get_app_data_dir() / "settings.json"

def get_app_version_file() -> Path:
    return get_app_data_dir() / "VERSION.txt"

def get_log_file() -> Path:
    return get_logs_dir() / "localjournal.log"

def ensure_app_directories() -> bool:
    """Create all necessary directories if they don't exist."""
    directories = [
        get_app_data_dir(),
        get_app_backups_dir(),
        get_screenshots_dir(),
        get_logs_dir(),
        get_backups_dir(),
        get_issue_tracker_dir(),
    ]
    try:
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory verified: {directory}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        return False


# Quick test — run: python utils/paths.py
if __name__ == "__main__":
    print(f"OS:           {platform.system()}")
    print(f"Desktop:      {get_desktop_path()}")
    print(f"Data dir:     {get_app_data_dir()}")
    print(f"Database:     {get_database_path()}")
    print(f"Desktop exists: {get_desktop_path().exists()}")


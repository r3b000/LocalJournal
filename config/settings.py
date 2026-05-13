"""
User settings and application state management
"""

import json
from pathlib import Path
from typing import Any, Optional


class Settings:
    """Application settings manager"""
    
    def __init__(self):
        self.settings_file = None
        self.settings = self._get_default_settings()
    
    def initialize(self, settings_path: Path):
        """Initialize settings with file path"""
        self.settings_file = settings_path
        self.settings = self._load_settings()
    
    def _load_settings(self) -> dict:
        """Load settings from file"""
        if self.settings_file and self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return self._get_default_settings()
        return self._get_default_settings()
    
    def _get_default_settings(self) -> dict:
        """Get default settings"""
        return {
            "theme": "dark",
            "default_account": None,
            "auto_backup": True,
            "backup_interval_days": 7,
            "disclaimer_accepted": False,
            "first_launch": True
        }
    
    def save_settings(self) -> bool:
        """Save settings to file"""
        if not self.settings_file:
            return False
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            return True
        except Exception:
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set setting value"""
        self.settings[key] = value
        return self.save_settings()
    
    def is_first_launch(self) -> bool:
        """Check if this is the first launch"""
        return self.settings.get("first_launch", True)
    
    def mark_launched(self) -> bool:
        """Mark app as launched"""
        return self.set("first_launch", False)
    
    def is_disclaimer_accepted(self) -> bool:
        """Check if disclaimer was accepted"""
        return self.settings.get("disclaimer_accepted", False)
    
    def accept_disclaimer(self) -> bool:
        """Mark disclaimer as accepted"""
        return self.set("disclaimer_accepted", True)


# Global settings instance (will be initialized in app.py)
app_settings = Settings()

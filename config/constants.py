"""
Application constants and configuration values
"""

# Application Info
APP_NAME = "LocalJournal"
APP_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"

# Database
DB_NAME = "localjournal.db"
DATA_FOLDER_NAME = "LocalJournalData"
BACKUP_FOLDER_NAME = "LocalJournal_Backups"

# Trade Directions
TRADE_DIRECTIONS = ["LONG", "SHORT"]

# Trade Status
TRADE_STATUS = ["OPEN", "CLOSED"]

# Grade Options
GRADE_OPTIONS = ["A+","A", "B", "C", "D", "F"]

# Screenshot Types
SCREENSHOT_TYPES = ["ENTRY", "EXIT", "OTHER"]

# Mental Development Categories
MENTAL_CATEGORIES = [
    "Trade Execution",
    "Risk Management",
    "Trade Management"
]

# Issue Types by Category
EXECUTION_ISSUES = [
    "Entered Too Early",
    "Entered Too Late",
    "Missed Planned Trade",
    "Took Unplanned Trade",
    "Failed To Act"
]

RISK_ISSUES = [
    "Poor R:R setup",
    "Undersized",
    "Oversized",
    "Ignored Volatility Adjusted Size",
    "Breached Daily Limit Loss",
    "Breached Weekly Limit Loss"
]

MANAGEMENT_ISSUES = [
    "Exited Too Early",
    "Exited Too Late",
    "Failed to take Profit at Level",
    "Adjusted Stop Unnecessarily",
    "Round-tripped for a Loss",
    "Round-tripped for B/E"
]

# Emotions List
EMOTIONS = [
    "Fear",
    "Greed",
    "Anxiety",
    "Confidence",
    "Hope",
    "FOMO",
    "Euphoria",
    "Frustration",
    "Anger",
    "Impatience",
    "Regret",
    "Boredom",
    "Overconfidence",
    "Revenge"
]

# Trading Environment Options
TRADING_ENVIRONMENTS = [
    "Trending UP",
    "Trending DOWN",      
    "Trend Shift", 
    "Ranging",
    "High Volatility",
    "Low Volatility",
    "Choppy",
    "Pre/Post News",
]

# Mental Development Worksheet Trigger
WORKSHEET_TRIGGER_COUNT = 5

# Date Formats
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
BACKUP_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# File Limits
MAX_SCREENSHOT_SIZE_MB = 10
MAX_BACKUP_SIZE_MB = 200

# Disclaimer
DISCLAIMER_TEXT = """
## LocalJournal Trading Application - Terms of Use

**IMPORTANT: READ CAREFULLY BEFORE USING THIS APPLICATION**

### Educational Purpose Only
This application is provided for **educational and informational purposes only**. It is designed to help traders log and analyze their trading activities. This software does not provide financial advice, trading signals, or investment recommendations.

### No Warranties
This software is provided **"AS IS"** without any warranties, express or implied, including but not limited to:
- Warranties of merchantability
- Fitness for a particular purpose
- Non-infringement
- Accuracy or reliability of data
- Uninterrupted or error-free operation

### Trading Risks
Trading in financial markets involves substantial risk of loss and is not suitable for every investor. You acknowledge that:
- Past performance does not guarantee future results
- Trading carries significant financial risks
- You are solely responsible for all trading decisions
- You should only trade with capital you can afford to lose

### No Developer Liability
The developers, contributors, and distributors of LocalJournal:
- Are not responsible for any trading losses or financial damages
- Do not guarantee the accuracy of calculations or data
- Are not liable for data loss, corruption, or software malfunctions
- Accept no responsibility for how you use this software
- Provide no technical support or guarantee of updates

### Data Responsibility
You are solely responsible for:
- Backing up your trading data regularly
- Maintaining the security of your data
- Verifying the accuracy of all logged information
- Any consequences resulting from data loss or corruption

### User Acknowledgment
By clicking "I Accept and Understand" below, you acknowledge that:
1. You have read and understood this disclaimer
2. You accept full responsibility for your use of this software
3. You will not hold the developers liable for any losses or damages
4. You understand the risks associated with trading
5. You use this software entirely at your own risk

### License
This software is open source. You may modify and distribute it, but you must retain this disclaimer and cannot hold the original developers liable for any modifications.

---

**If you do not agree with these terms, do not use this application.**
"""

# UI Configuration
SIDEBAR_WIDTH = 280
MAX_RECENT_TRADES = 5
DEFAULT_CHART_HEIGHT = 400
TABLE_PAGE_SIZE = 50

# Logging
LOG_FILE_NAME = "localjournal.log"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

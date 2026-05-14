<div align="center">

# 📓 LocalJournal

**A professional trading journal — 100% local, 100% private.**

[![Version](https://img.shields.io/badge/version-1.0.0-7e3abe?style=for-the-badge)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-ff4b4b?style=for-the-badge&logo=streamlit)](https://streamlit.io/)

*Log trades. Analyze performance. Grow as a trader. No internet required.*

</div>

---

## ✨ Overview

LocalJournal is a **desktop trading journal application** built with Python and Streamlit. Every single byte of your trading data stays on your own machine — no cloud, no subscriptions, no tracking. It runs as a native desktop app via `pywebview` and launches silently with a single double-click.

---

## 🚀 Features

### 📊 Comprehensive Trade Logging
- Multi-entry and multi-exit support with weighted average calculations
- Position sizing calculator with risk management
- R-multiple tracking and prospective risk calculations
- Trade grading system (mental + technical execution: A+, A, B, C, D, F)
- Screenshot attachment system per trade (Entry / Exit / Other)

### 📈 Advanced Statistics & Analytics
- Win rate, profit factor, expectancy calculations
- R-multiple distribution analysis
- Equity curve visualization
- Performance breakdown by symbol, strategy, and direction
- Calendar heatmap for daily performance
- Streak analysis (winning and losing streaks)
- Risk metrics: Sharpe ratio, max drawdown, recovery factor

### 🧠 Mental Development Tracker
- Three categories: Trade Execution · Risk Management · Trade Management
- Automatic worksheet trigger after 5 pattern occurrences
- Emotion tracker (Fear, Greed, FOMO, Anxiety, and more)
- Actionable improvement worksheets

### 🗄️ Data Management
- SQLite local database with ACID compliance
- Automated backup system
- Manual backup creation with timestamps
- Database import/export functionality
- Data integrity checks

### 🔒 Privacy First
- 100% local data storage on your Desktop
- No internet connection required
- No analytics, telemetry, or data transmission
- No accounts, no sign-ups

---

## 🖥️ Pages

| Page | Description |
|---|---|
| 🏠 **Home** | Welcome screen and quick-start guide |
| 📊 **Dashboard** | Account overview, equity curve, recent trades |
| 💼 **Accounts** | Multi-account management |
| 📝 **Log Trade** | Open and close trades with full detail |
| 📋 **Trade History** | Full trade log with filters |
| 🧠 **Mental Development** | Psychology tracking and worksheets |
| ♟️ **Strategies** | Strategy management system |
| 📈 **Statistics** | Advanced analytics and reports |
| 💾 **Data Management** | Backups, export, import |

---

## 📁 Project Structure

```
LocalJournal/
├── app.py                    # Main Streamlit entry point
├── run_app.py                # Desktop launcher (pywebview)
├── start_desktop.bat         # Windows batch launcher
├── LocalJournal.vbs          # Silent launcher (no terminal window)
├── requirements.txt          # Python dependencies
├── VERSION.txt               # Current version
│
├── .streamlit/
│   └── config.toml           # Streamlit theme (dark purple)
│
├── assets/                   # Icons and images
│
├── components/               # Reusable UI components
│   ├── account_selector.py
│   ├── filters.py
│   ├── grade_selector.py
│   └── position_calculator.py
│
├── config/                   # App configuration
│   ├── constants.py          # App-wide constants
│   └── settings.py           # User settings manager
│
├── database/                 # Database layer
│   ├── schema.py             # Table definitions
│   ├── connection.py         # SQLite connection manager
│   ├── accounts_db.py
│   ├── trades_db.py
│   ├── mental_db.py
│   ├── statistics_db.py
│   ├── strategies_db.py
│   └── migrations/           # Schema migration scripts
│
├── pages/                    # Streamlit multi-page app
│   ├── 1_Dashboard.py
│   ├── 2_Accounts.py
│   ├── 3_LogTrade.py
│   ├── 4_TradeHistory.py
│   ├── 5_MentalDevelopment.py
│   ├── 6_Strategies.py
│   ├── 7_Statistics.py
│   └── 8_DataManagement.py
│
└── utils/                    # Utility functions
    ├── calculations.py
    ├── formatters.py
    ├── validators.py
    ├── logger.py
    ├── paths.py
    ├── cache_manager.py
    ├── screenshot_manager.py
    └── session_state.py
```

---

## ⚙️ Installation

### Prerequisites
- Python **3.11** or higher
- Windows 10 / 11

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/YOUR-USERNAME/LocalJournal.git
cd LocalJournal

# 2. Create a virtual environment with Python 3.11
py -3.11 -m venv .venv

# 3. Activate the virtual environment
.venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the app
streamlit run app.py
```

### Launch as Desktop App (no terminal)

Double-click **`LocalJournal.vbs`** — the app will open in a native desktop window with no console.

---

## 📦 Requirements

```
streamlit>=1.40.0
pywebview>=5.1
pandas>=2.2.3
numpy>=2.2.1
pillow>=11.0.0
plotly>=5.18.0
openpyxl>=3.1.5
python-dateutil>=2.9.0
altair>=5
python-docx>=1.2.0
```

---

## 🗂️ Data Storage

All data is saved locally on your machine:

```
Desktop/
├── LocalJournalData/
│   ├── localjournal.db           # Main SQLite database
│   ├── screenshots/              # Trade screenshots
│   ├── issue_tracker/            # Mental development worksheets
│   ├── logs/                     # App logs
│   └── backups/                  # Auto-backups
│
└── LocalJournalBackups/          # Manual backups
```

---

## 🤝 Contributing

LocalJournal is public for viewing, cloning, and personal use.

Direct contributions to the official repository are maintainer-controlled.  
If you want to contribute, please contact the maintainer first and ask for approval before opening a pull request or requesting collaborator access.

Unapproved pull requests may be declined.

For full contribution rules, see [CONTRIBUTING.md](CONTRIBUTING.md).


---

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full version history.

---

## ⚠️ Disclaimer

LocalJournal is provided for **educational and informational purposes only**. It does not provide financial advice, trading signals, or investment recommendations. Trading in financial markets involves substantial risk. You are solely responsible for all trading decisions.

See the full disclaimer inside the application on first launch.

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">

Made with ❤️ for traders who value privacy.

⭐ If LocalJournal helps your trading, please star the repo!

</div>

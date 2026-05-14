# Changelog

All notable changes to LocalJournal will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-02-14

### Fixed
- Fixed database/data folder path detection so LocalJournal correctly resolves the user Desktop location across Windows, macOS, and Linux.
- Fixed an issue where Windows systems using OneDrive Desktop redirection could create or detect the database in the wrong location.

## [1.0.0] - 2026-02-13

### Initial Release

#### Added
- Core trading journal functionality with comprehensive trade logging
- Multi-account management system
- Position sizing calculator with risk management
- Multi-entry and multi-exit trade support with weighted averages
- R-multiple tracking and prospective risk calculations
- Trade grading system (mental and technical execution)
- Screenshot attachment system for trade documentation
- Mental development tracking with three categories:
  - Trade Execution issues
  - Risk Management issues
  - Trade Management issues
- Automatic worksheet triggers after 5 pattern occurrences
- Dual-tracker system for emotions and issue types
- Advanced statistics and analytics:
  - Win rate, profit factor, expectancy calculations
  - R-multiple distribution analysis
  - Equity curve visualization
  - Performance breakdown by symbol, strategy, and direction
  - Calendar heatmap for daily performance
  - Streak analysis (winning and losing)
  - Risk metrics (Sharpe ratio, max drawdown, recovery factor)
- Strategy management system
- Data management features:
  - SQLite local database with ACID compliance
  - Automated backup system
  - Manual backup creation with timestamps
  - Database import/export functionality
  - Data integrity checks
- Desktop application mode with pywebview
- Dark theme with purple accent color
- Comprehensive logging system
- Session state management
- Input validation and error handling

#### Technical Implementation
- Streamlit-based user interface
- SQLite database with proper foreign key constraints
- Modular architecture with separated concerns:
  - Database operations layer
  - Business logic layer
  - UI components layer
  - Utility functions layer
- Performance optimizations:
  - Caching strategy with TTL
  - Database indexing for fast queries
  - SQL window functions for running totals
- Local-first architecture with no external dependencies
- Professional file structure and code organization

#### Security & Privacy
- 100% local data storage
- No internet connection required
- No analytics or telemetry
- No data transmission to external servers

---

## Version Format

- **MAJOR.MINOR.PATCH** (Semantic Versioning)
- **MAJOR**: Breaking changes or major feature additions
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes and minor improvements

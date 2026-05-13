"""
Safe Index Migration Script for LocalJournal
Adds performance indexes to existing database without breaking anything
"""

import sqlite3
from pathlib import Path
import time
from datetime import datetime
import sys


class IndexMigration:
    def __init__(self, db_path):
        self.db_path = db_path
        self.indexes_added = []
        self.indexes_skipped = []
    
    def add_index_safely(self, cursor, index_name, create_statement):
        """Add index with error handling"""
        try:
            # Check if index already exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name=?
            """, (index_name,))
            
            if cursor.fetchone():
                self.indexes_skipped.append(index_name)
                print(f"  [ SKIP ] {index_name} (already exists)")
                return True
            
            # Create index
            start = time.time()
            cursor.execute(create_statement)
            duration = (time.time() - start) * 1000
            
            self.indexes_added.append(index_name)
            print(f"  [ OK ] {index_name} ({duration:.0f}ms)")
            return True
            
        except Exception as e:
            print(f"  [ X ] {index_name} - {e}")
            return False
    
    def run_migration(self):
        """Run the complete index migration"""
        print("=" * 70)
        print("LOCALJOURNAL INDEX MIGRATION")
        print("=" * 70)
        print(f"Database: {self.db_path}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 70)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Get database info
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        size_before = cursor.fetchone()[0]
        
        print(f"\nDatabase info:")
        print(f"  - Trades: {trade_count}")
        print(f"  - Size: {size_before / 1024:.1f} KB")
        print()
        
        total_start = time.time()
        
        # TRADES TABLE INDEXES
        print("[ PHASE 1 ] Trades Table Indexes")
        print("-" * 70)
        
        trades_indexes = [
            ("idx_trades_direction", "CREATE INDEX IF NOT EXISTS idx_trades_direction ON trades(direction)"),
            ("idx_trades_pnl", "CREATE INDEX IF NOT EXISTS idx_trades_pnl ON trades(pnl)"),
            ("idx_trades_grades", "CREATE INDEX IF NOT EXISTS idx_trades_grades ON trades(grade_mentally, grade_technically)"),
            ("idx_trades_account_entry_date", "CREATE INDEX IF NOT EXISTS idx_trades_account_entry_date ON trades(account_id, entry_date DESC)"),
            ("idx_trades_account_status_date", "CREATE INDEX IF NOT EXISTS idx_trades_account_status_date ON trades(account_id, status, entry_date DESC)"),
            ("idx_trades_account_symbol", "CREATE INDEX IF NOT EXISTS idx_trades_account_symbol ON trades(account_id, symbol)"),
            ("idx_trades_account_direction", "CREATE INDEX IF NOT EXISTS idx_trades_account_direction ON trades(account_id, direction)"),
            ("idx_trades_account_status_entry", "CREATE INDEX IF NOT EXISTS idx_trades_account_status_entry ON trades(account_id, status, entry_date, entry_time)"),
            ("idx_trades_equity_curve", "CREATE INDEX IF NOT EXISTS idx_trades_equity_curve ON trades(account_id, status, entry_date, entry_time, pnl)"),
        ]
        
        for index_name, create_sql in trades_indexes:
            self.add_index_safely(cursor, index_name, create_sql)
        
        # MENTAL_ISSUES TABLE INDEXES
        print("\n[ PHASE 2 ] Mental Issues Table Indexes")
        print("-" * 70)
        
        mental_indexes = [
            ("idx_mental_emotion", "CREATE INDEX IF NOT EXISTS idx_mental_emotion ON mental_issues(emotion)"),
            ("idx_mental_logged_at", "CREATE INDEX IF NOT EXISTS idx_mental_logged_at ON mental_issues(logged_at DESC)"),
        ]
        
        for index_name, create_sql in mental_indexes:
            self.add_index_safely(cursor, index_name, create_sql)
        
        # SCREENSHOTS TABLE INDEXES
        print("\n[ PHASE 3 ] Screenshots Table Indexes")
        print("-" * 70)
        
        screenshot_indexes = [
            ("idx_screenshots_type", "CREATE INDEX IF NOT EXISTS idx_screenshots_type ON screenshots(screenshot_type)"),
        ]
        
        for index_name, create_sql in screenshot_indexes:
            self.add_index_safely(cursor, index_name, create_sql)
        
        # Commit changes
        conn.commit()
        
        # Get database size after
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        size_after = cursor.fetchone()[0]
        
        # Analyze for query planner optimization
        print("\n[ PHASE 4 ] Optimizing Query Planner")
        print("-" * 70)
        print("  Running ANALYZE command...")
        cursor.execute("ANALYZE")
        conn.commit()
        print("  [ OK ] Query planner optimized")
        
        conn.close()
        
        total_duration = (time.time() - total_start) * 1000
        
        # Print summary
        print("\n" + "=" * 70)
        print("MIGRATION COMPLETE")
        print("=" * 70)
        print(f"Total time: {total_duration:.0f}ms")
        print(f"Indexes added: {len(self.indexes_added)}")
        print(f"Indexes skipped: {len(self.indexes_skipped)}")
        print(f"Database size: {size_before / 1024:.1f} KB → {size_after / 1024:.1f} KB")
        print(f"Size increase: {(size_after - size_before) / 1024:.1f} KB")
        
        print("\n" + "=" * 70)
        print("[ SUCCESS ] Your database is now optimized!")
        print("=" * 70)
        
        return True


if __name__ == "__main__":
    # Try to find database
    db_paths = [
        Path.home() / "Desktop" / "LocalJournalData" / "localjournal.db",
        Path("localjournal.db"),
        Path("LocalJournalData") / "localjournal.db"
    ]
    
    db_path = None
    for path in db_paths:
        if path.exists():
            db_path = path
            break
    
    if not db_path:
        print("[ ERROR ] Could not find localjournal.db")
        sys.exit(1)
    
    # Confirm before proceeding
    print("\n" + "=" * 70)
    print("DATABASE INDEX MIGRATION")
    print("=" * 70)
    print("This will add performance indexes to your database.")
    print("Operation is safe and non-destructive.")
    print()
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n[ CANCELLED ] Migration aborted")
        sys.exit(0)
    
    print()
    
    # Run migration
    migrator = IndexMigration(db_path)
    migrator.run_migration()

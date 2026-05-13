"""
Migration: Recalculate total_r for all closed trades using PnL / risk_amount.
Run once: python -m database.migrations.recalculate_total_r
"""
from pathlib import Path
from database.connection import get_db_connection
from utils.paths import get_database_path
import logging

logger = logging.getLogger(__name__)


def recalculate_total_r(db_path: Path) -> int:
    """
    Recalculates total_r for every closed trade using pnl / risk_amount.
    Returns count of trades updated.
    """
    updated = 0
    skipped = 0

    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT trade_id, pnl, risk_amount, total_r
                FROM trades
                WHERE status = 'CLOSED'
                  AND pnl IS NOT NULL
                  AND risk_amount IS NOT NULL
                  AND risk_amount > 0
            """)
            trades = cursor.fetchall()

            for row in trades:
                trade_id, pnl, risk_amount, old_r = row
                correct_r = round(pnl / risk_amount, 4)

                cursor.execute(
                    "UPDATE trades SET total_r = ? WHERE trade_id = ?",
                    (correct_r, trade_id)
                )
                print(f"  Trade #{trade_id}: {old_r} → {correct_r}")
                updated += 1

            print(f"\n[OK] Updated {updated} trades. Skipped {skipped}.")
        return updated

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"[ERROR] {e}")
        return 0


if __name__ == "__main__":
    db_path = get_database_path()
    print(f"Recalculating total_r for: {db_path}\n")
    recalculate_total_r(db_path)

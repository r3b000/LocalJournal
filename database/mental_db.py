"""
Mental development database operations
Handles CRUD operations for mental issues and worksheets
"""

from pathlib import Path
from typing import Optional, List, Dict, Tuple
import logging
from datetime import datetime
from database.connection import get_db_connection, fetch_one, fetch_all
from config.constants import WORKSHEET_TRIGGER_COUNT
from utils.paths import get_issue_tracker_dir

logger = logging.getLogger(__name__)


def log_mental_issue(db_path: Path, account_id: int, issue_category: str,
                     issue_type: str, emotion: str, comments: str = None,
                     trade_id: int = None) -> Tuple[Optional[int], bool, Optional[str], Optional[str]]:
    """Log a mental development issue and check if worksheet should be triggered"""
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mental_issues (account_id, trade_id, issue_category, issue_type, emotion, comments)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (account_id, trade_id, issue_category, issue_type, emotion, comments))
            issue_id = cursor.lastrowid
            should_show_worksheet, trigger_type, trigger_value = _update_trackers(
                cursor, account_id, issue_category, issue_type, emotion
            )
            logger.info(f"Mental issue logged: {issue_category} - {issue_type} - {emotion}")
            return issue_id, should_show_worksheet, trigger_type, trigger_value
    except Exception as e:
        logger.error(f"Failed to log mental issue: {e}")
        return None, False, None, None


def _update_trackers(cursor, account_id: int, issue_category: str,
                    issue_type: str, emotion: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Update both emotion and issue trackers"""
    emotion_triggered = _update_emotion_tracker(cursor, account_id, issue_category, emotion)
    issue_triggered = _update_issue_tracker(cursor, account_id, issue_category, issue_type)
    if emotion_triggered:
        return True, "EMOTION", emotion
    elif issue_triggered:
        return True, "ISSUE", issue_type
    else:
        return False, None, None


def _update_emotion_tracker(cursor, account_id: int, issue_category: str, emotion: str) -> bool:
    """
    Update emotion tracker and check if worksheet should be shown
    
    FIXED: Check worksheet_completed status BEFORE incrementing
    """
    cursor.execute("""
        SELECT emotion_tracker_id, occurrence_count, worksheet_completed
        FROM emotion_trackers
        WHERE account_id = ? AND issue_category = ? AND emotion = ?
    """, (account_id, issue_category, emotion))
    tracker = cursor.fetchone()
    
    if tracker:
        tracker_id, current_count, worksheet_completed = tracker[0], tracker[1], tracker[2]
        new_count = current_count + 1
        
        # Update tracker
        cursor.execute("""
            UPDATE emotion_trackers
            SET occurrence_count = ?,
                last_occurred = CURRENT_TIMESTAMP
            WHERE emotion_tracker_id = ?
        """, (new_count, tracker_id))
        
        # FIXED: Check if we've reached threshold AND worksheet not already pending
        if new_count >= WORKSHEET_TRIGGER_COUNT and worksheet_completed == 0:
            # Mark as pending worksheet
            cursor.execute("""
                UPDATE emotion_trackers
                SET worksheet_completed = 1
                WHERE emotion_tracker_id = ?
            """, (tracker_id,))
            logger.info(f"Emotion worksheet trigger: {emotion} in {issue_category} ({new_count} times)")
            return True
    else:
        # Create new emotion tracker
        cursor.execute("""
            INSERT INTO emotion_trackers (account_id, issue_category, emotion, occurrence_count, last_occurred, worksheet_completed)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP, 0)
        """, (account_id, issue_category, emotion))
    
    return False


def _update_issue_tracker(cursor, account_id: int, issue_category: str, issue_type: str) -> bool:
    """
    Update issue tracker and check if worksheet should be shown
    
    FIXED: Check worksheet_completed status BEFORE incrementing
    """
    cursor.execute("""
        SELECT issue_tracker_id, occurrence_count, worksheet_completed
        FROM issue_trackers
        WHERE account_id = ? AND issue_category = ? AND issue_type = ?
    """, (account_id, issue_category, issue_type))
    tracker = cursor.fetchone()
    
    if tracker:
        tracker_id, current_count, worksheet_completed = tracker[0], tracker[1], tracker[2]
        new_count = current_count + 1
        
        # Update tracker
        cursor.execute("""
            UPDATE issue_trackers
            SET occurrence_count = ?,
                last_occurred = CURRENT_TIMESTAMP
            WHERE issue_tracker_id = ?
        """, (new_count, tracker_id))
        
        # FIXED: Check if we've reached threshold AND worksheet not already pending
        if new_count >= WORKSHEET_TRIGGER_COUNT and worksheet_completed == 0:
            # Mark as pending worksheet
            cursor.execute("""
                UPDATE issue_trackers
                SET worksheet_completed = 1
                WHERE issue_tracker_id = ?
            """, (tracker_id,))
            logger.info(f"Issue worksheet trigger: {issue_type} in {issue_category} ({new_count} times)")
            return True
    else:
        # Create new issue tracker
        cursor.execute("""
            INSERT INTO issue_trackers (account_id, issue_category, issue_type, occurrence_count, last_occurred, worksheet_completed)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP, 0)
        """, (account_id, issue_category, issue_type))
    
    return False


def save_worksheet(db_path: Path, account_id: int, issue_category: str,
                   trigger_type: str, trigger_value: str, occurrence_count: int,
                   worksheet_data: Dict) -> bool:
    """
    Save completed worksheet and reset appropriate tracker
    
    FIXED: Reset both occurrence_count AND worksheet_completed to 0
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mental_worksheets (
                    account_id, issue_category, trigger_type, trigger_value, occurrence_count,
                    emotional_pattern, root_cause, challenge_response, action_plan, expected_outcome
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (account_id, issue_category, trigger_type, trigger_value, occurrence_count,
                  worksheet_data.get('emotional_pattern'), worksheet_data.get('root_cause'),
                  worksheet_data.get('challenge_response'), worksheet_data.get('action_plan'),
                  worksheet_data.get('expected_outcome')))
            worksheet_id = cursor.lastrowid
            
            # Reset tracker based on type
            if trigger_type == "EMOTION":
                _reset_emotion_tracker(cursor, account_id, issue_category, trigger_value)
            elif trigger_type == "ISSUE":
                _reset_issue_tracker(cursor, account_id, issue_category, trigger_value)
            else:
                logger.error(f"Invalid trigger_type: {trigger_type}")
                return False
            
            _save_worksheet_file(account_id, issue_category, trigger_type, trigger_value, occurrence_count, worksheet_data)
            logger.info(f"Worksheet saved: ID {worksheet_id}, {issue_category} - {trigger_type}:{trigger_value}")
            return True
    except Exception as e:
        logger.error(f"Failed to save worksheet: {e}")
        return False


def _reset_emotion_tracker(cursor, account_id: int, issue_category: str, emotion: str):
    """
    Reset emotion tracker after worksheet completion
    
    FIXED: Reset BOTH occurrence_count AND worksheet_completed to 0
    This allows the tracker to trigger again after 5 more occurrences
    """
    cursor.execute("""
        UPDATE emotion_trackers
        SET occurrence_count = 0,
            worksheet_completed = 0,
            last_reset = CURRENT_TIMESTAMP
        WHERE account_id = ? AND issue_category = ? AND emotion = ?
    """, (account_id, issue_category, emotion))
    logger.info(f"Emotion tracker reset: {emotion} in {issue_category} - Ready for next cycle")


def _reset_issue_tracker(cursor, account_id: int, issue_category: str, issue_type: str):
    """
    Reset issue tracker after worksheet completion
    
    FIXED: Reset BOTH occurrence_count AND worksheet_completed to 0
    This allows the tracker to trigger again after 5 more occurrences
    """
    cursor.execute("""
        UPDATE issue_trackers
        SET occurrence_count = 0,
            worksheet_completed = 0,
            last_reset = CURRENT_TIMESTAMP
        WHERE account_id = ? AND issue_category = ? AND issue_type = ?
    """, (account_id, issue_category, issue_type))
    logger.info(f"Issue tracker reset: {issue_type} in {issue_category} - Ready for next cycle")


def reset_tracker_without_worksheet(db_path: Path, account_id: int, issue_category: str,
                                    trigger_type: str, trigger_value: str) -> bool:
    """
    Reset tracker counter without saving a worksheet
    Used when user dismisses worksheet modal
    
    FIXED: Reset BOTH occurrence_count AND worksheet_completed to 0
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            if trigger_type == "EMOTION":
                cursor.execute("""
                    UPDATE emotion_trackers
                    SET occurrence_count = 0,
                        worksheet_completed = 0,
                        last_reset = CURRENT_TIMESTAMP
                    WHERE account_id = ? AND issue_category = ? AND emotion = ?
                """, (account_id, issue_category, trigger_value))
                logger.info(f"Emotion tracker reset without worksheet: {trigger_value} in {issue_category}")
                
            elif trigger_type == "ISSUE":
                cursor.execute("""
                    UPDATE issue_trackers
                    SET occurrence_count = 0,
                        worksheet_completed = 0,
                        last_reset = CURRENT_TIMESTAMP
                    WHERE account_id = ? AND issue_category = ? AND issue_type = ?
                """, (account_id, issue_category, trigger_value))
                logger.info(f"Issue tracker reset without worksheet: {trigger_value} in {issue_category}")
                
            else:
                logger.error(f"Invalid trigger_type: {trigger_type}")
                return False
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to reset tracker: {e}")
        return False


def _save_worksheet_file(account_id: int, issue_category: str, trigger_type: str,
                        trigger_value: str, occurrence_count: int, worksheet_data: Dict):
    """Save worksheet as text file"""
    try:
        worksheet_dir = get_issue_tracker_dir()
        worksheet_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        category_clean = issue_category.replace(' ', '_')
        value_clean = trigger_value.replace(' ', '_')
        filename = f"worksheet_{category_clean}_{trigger_type}_{value_clean}_{timestamp}.txt"
        filepath = worksheet_dir / filename
        content = f"""
MENTAL DEVELOPMENT WORKSHEET
============================
Account ID: {account_id}
Issue Category: {issue_category}
Trigger Type: {trigger_type}
Trigger Value: {trigger_value}
Occurrence Count: {occurrence_count}
Completed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---
A. IDENTIFY THE ISSUE
{worksheet_data.get('emotional_pattern', '')}

---
B. UNDERSTANDING THE ROOT CAUSE
{worksheet_data.get('root_cause', '')}

---
C. CHALLENGE YOUR ISSUE
{worksheet_data.get('challenge_response', '')}

---
D. ACTION PLAN FOR IMPROVEMENT
{worksheet_data.get('action_plan', '')}

---
E. EXPECTED OUTCOME AND FUTURE APPROACH
{worksheet_data.get('expected_outcome', '')}
============================
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Worksheet file saved: {filename}")
    except Exception as e:
        logger.error(f"Failed to save worksheet file: {e}")


def get_all_issues(db_path: Path, account_id: int) -> List[Dict]:
    """Get all mental issues for an account"""
    query = """
        SELECT issue_id, account_id, trade_id, issue_category, issue_type,
               emotion, comments, logged_at
        FROM mental_issues WHERE account_id = ? ORDER BY logged_at DESC
    """
    return fetch_all(db_path, query, (account_id,))


def get_completed_worksheets(db_path: Path, account_id: int) -> List[Dict]:
    """Get all completed worksheets for an account"""
    query = """
        SELECT worksheet_id, account_id, issue_category, trigger_type, trigger_value,
               occurrence_count, emotional_pattern, root_cause, challenge_response,
               action_plan, expected_outcome, completed_at
        FROM mental_worksheets WHERE account_id = ? ORDER BY completed_at DESC
    """
    return fetch_all(db_path, query, (account_id,))


def get_issue_summary(db_path: Path, account_id: int) -> Dict:
    """Get summary of issues by category"""
    query = """
        SELECT issue_category, COUNT(*) as count
        FROM mental_issues WHERE account_id = ? GROUP BY issue_category
    """
    results = fetch_all(db_path, query, (account_id,))
    summary = {'Trade Execution': 0, 'Risk Management': 0, 'Trade Management': 0, 'total': 0}
    for row in results:
        summary[row['issue_category']] = row['count']
        summary['total'] += row['count']
    return summary


def delete_mental_issue(db_path: Path, issue_id: int) -> bool:
    """
    Delete a mental issue by ID
    
    Args:
        db_path: Path to database
        issue_id: Issue ID to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM mental_issues
                WHERE issue_id = ?
            """, (issue_id,))
            
            if cursor.rowcount > 0:
                logger.info(f"Mental issue deleted: ID {issue_id}")
                return True
            else:
                logger.warning(f"Mental issue not found: ID {issue_id}")
                return False
                
    except Exception as e:
        logger.error(f"Failed to delete mental issue {issue_id}: {e}")
        return False


def delete_mental_worksheet(db_path: Path, worksheet_id: int, account_id: int) -> bool:
    """
    Delete a mental worksheet by ID and its corresponding file
    
    Args:
        db_path: Path to database
        worksheet_id: Worksheet ID to delete
        account_id: Account ID for file lookup
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT issue_category, trigger_type, trigger_value, completed_at
                FROM mental_worksheets
                WHERE worksheet_id = ? AND account_id = ?
            """, (worksheet_id, account_id))
            
            worksheet = cursor.fetchone()
            
            if not worksheet:
                logger.warning(f"Worksheet not found: ID {worksheet_id}")
                return False
            
            issue_category = worksheet[0]
            trigger_type = worksheet[1]
            trigger_value = worksheet[2]
            completed_at = worksheet[3]
            
            cursor.execute("""
                DELETE FROM mental_worksheets
                WHERE worksheet_id = ?
            """, (worksheet_id,))
            
            if cursor.rowcount > 0:
                issue_tracker_dir = get_issue_tracker_dir()
                
                if issue_tracker_dir and issue_tracker_dir.exists():
                    timestamp = completed_at[:10].replace('-', '')
                    
                    safe_category = issue_category.replace(' ', '_')
                    safe_trigger = trigger_value.replace(' ', '_')
                    
                    pattern = f"{safe_category}_{trigger_type}_{safe_trigger}_{timestamp}*.txt"
                    
                    for file_path in issue_tracker_dir.glob(pattern):
                        try:
                            file_path.unlink()
                            logger.info(f"Deleted worksheet file: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to delete worksheet file {file_path}: {e}")
                
                logger.info(f"Mental worksheet deleted: ID {worksheet_id}")
                return True
            else:
                return False
                
    except Exception as e:
        logger.error(f"Failed to delete mental worksheet {worksheet_id}: {e}")
        return False

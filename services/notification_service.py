from typing import List, Dict, Any, Optional
from database import get_db_connection

def create_notification(user_id: int, title: str, message: str, link: Optional[str] = None) -> int:
    """Inserts an in-app notification for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notifications (user_id, title, message, link, is_read)
        VALUES (?, ?, ?, ?, 0)
    ''', (user_id, title.strip(), message.strip(), link))
    notif_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return notif_id

def get_user_notifications(user_id: int, limit: int = 25) -> List[Dict[str, Any]]:
    """Fetches notifications for a user ordered by most recent first."""
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT * FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_unread_notification_count(user_id: int) -> int:
    """Returns the total number of unread notifications for a user."""
    conn = get_db_connection()
    row = conn.execute('''
        SELECT COUNT(*) as c FROM notifications
        WHERE user_id = ? AND is_read = 0
    ''', (user_id,)).fetchone()
    conn.close()
    return row['c'] if row else 0

def mark_notification_as_read(notification_id: int, user_id: int) -> bool:
    """Marks a single notification as read."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE notifications SET is_read = 1
        WHERE id = ? AND user_id = ?
    ''', (notification_id, user_id))
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected

def mark_all_notifications_as_read(user_id: int) -> int:
    """Marks all notifications for a user as read."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE notifications SET is_read = 1
        WHERE user_id = ? AND is_read = 0
    ''', (user_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected

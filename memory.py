"""
memory.py
Handles all database operations using SQLite for the web app.

The web version tracks DAILY records per user (one row per user per day)
so we can show a history/streak, in addition to the running totals.
"""

import sqlite3
import datetime

DB_NAME = "medication.db"


def init_db():
    """
    Creates the database and tables if they don't already exist.

    users:       one row per registered person
    daily_log:   one row per user per calendar day, tracking status
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            medication_name TEXT,
            dose_time TEXT,
            missed_doses INTEGER DEFAULT 0,
            last_taken TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            log_date TEXT,
            status TEXT,
            UNIQUE(user_name, log_date)
        )
    """)

    conn.commit()
    conn.close()


def save_user(name, medication, dose_time):
    """
    Adds a new user, or updates medication/dose_time if the user already exists.
    Returns True if a new user was created, False if it already existed.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    created = False
    try:
        cursor.execute("""
            INSERT INTO users (name, medication_name, dose_time, missed_doses, last_taken)
            VALUES (?, ?, ?, 0, 'Never')
        """, (name, medication, dose_time))
        created = True
    except sqlite3.IntegrityError:
        cursor.execute("""
            UPDATE users SET medication_name = ?, dose_time = ?
            WHERE name = ?
        """, (medication, dose_time, name))
    conn.commit()
    conn.close()
    return created


def get_user(name):
    """
    Fetches a user's data by name. Returns a dict, or None if not found.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "medication_name": row[2],
        "dose_time": row[3],
        "missed_doses": row[4],
        "last_taken": row[5]
    }


def get_all_users():
    """
    Returns a list of all user names in the database.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM users ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]


def mark_dose_taken(name):
    """
    Marks today's dose as taken: resets missed_doses to 0,
    updates last_taken timestamp, and logs today as 'taken'.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.date.today().isoformat()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET missed_doses = 0, last_taken = ?
        WHERE name = ?
    """, (now, name))
    cursor.execute("""
        INSERT INTO daily_log (user_name, log_date, status)
        VALUES (?, ?, 'taken')
        ON CONFLICT(user_name, log_date) DO UPDATE SET status='taken'
    """, (name, today))
    conn.commit()
    conn.close()


def increment_missed_doses(name):
    """
    Increases missed_doses by 1 and logs today as 'missed'.
    """
    today = datetime.date.today().isoformat()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET missed_doses = missed_doses + 1
        WHERE name = ?
    """, (name,))
    cursor.execute("""
        INSERT INTO daily_log (user_name, log_date, status)
        VALUES (?, ?, 'missed')
        ON CONFLICT(user_name, log_date) DO UPDATE SET status='missed'
    """, (name, today))
    conn.commit()
    conn.close()


def get_today_status(name):
    """
    Returns today's logged status for a user: 'taken', 'missed', or None
    if no entry has been logged yet today.
    """
    today = datetime.date.today().isoformat()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status FROM daily_log WHERE user_name = ? AND log_date = ?
    """, (name, today))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_history(name, days=14):
    """
    Returns the last `days` days of log entries for a user as a list of
    (date_string, status) tuples, ordered oldest to newest.
    Days with no entry are returned with status 'none'.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT log_date, status FROM daily_log WHERE user_name = ?
    """, (name,))
    rows = dict(cursor.fetchall())
    conn.close()

    history = []
    today = datetime.date.today()
    for i in range(days - 1, -1, -1):
        d = today - datetime.timedelta(days=i)
        d_str = d.isoformat()
        status = rows.get(d_str, "none")
        history.append((d_str, status))
    return history

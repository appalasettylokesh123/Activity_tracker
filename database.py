
import sqlite3

import os

DB_NAME = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "activities.db"
)



def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            category TEXT,
            task_date TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            duration_seconds INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            reminder_at TEXT,
            reminder_sent INTEGER DEFAULT 0,
            timer_started_at TEXT
        )
    """) 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_name TEXT NOT NULL UNIQUE,
            category TEXT,
            active INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_activity_logs (
            activity_id INTEGER,
            activity_date TEXT,
            completed INTEGER DEFAULT 0,
            completed_at TEXT,

            PRIMARY KEY (activity_id, activity_date),

            FOREIGN KEY (activity_id)
            REFERENCES daily_activities(id)
        )
    """)

    # Insert default activities only once
    default_activities = [
        ("Wake up early", "Personal"),
        ("Morning Run", "Fitness"),
        ("Workout / Gym", "Fitness"),
        ("Read for 30 minutes", "Learning"),
        ("Python practice", "Learning"),
        ("DSA practice", "Learning"),
        ("Project development", "Projects"),
        
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO daily_activities
        (activity_name, category)
        VALUES (?, ?)
    """, default_activities)

    

    conn.commit()
    conn.close()

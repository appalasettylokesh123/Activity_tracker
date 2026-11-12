
import sqlite3
from datetime import datetime
from plyer import notification
from apscheduler.schedulers.background import BackgroundScheduler

from database import DB_NAME


def check_reminders():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    now = datetime.now().isoformat(timespec="seconds")

    cursor.execute("""
        SELECT id, task_name
        FROM tasks
        WHERE reminder_at IS NOT NULL
        AND reminder_at <= ?
        AND reminder_sent = 0
    """, (now,))

    reminders = cursor.fetchall()

    for task_id, task_name in reminders:

        try:
            notification.notify(
                title="Activity Reminder",
                message=f"Time to start: {task_name}",
                app_name="Daily Activity Tracker",
                timeout=10
            )

            cursor.execute("""
                UPDATE tasks
                SET reminder_sent = 1
                WHERE id = ?
            """, (task_id,))

        except Exception as error:
            print("Notification error:", error)

    conn.commit()
    conn.close()


scheduler = BackgroundScheduler()


def start_reminder_service():
    if not scheduler.running:
        scheduler.add_job(
            check_reminders,
            "interval",
            seconds=30,
            id="activity_reminders",
            replace_existing=True
        )

        scheduler.start()


from database import get_connection
from datetime import datetime, date, timedelta, timezone


# ==========================================
# 1. ADD A NEW TASK
# ==========================================

def add_task(name, category, task_date, start, end, reminder):

    conn = get_connection()

    conn.execute("""
        INSERT INTO tasks
        (task_name, category, task_date,
         start_time, end_time, reminder_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name, category, task_date,
        start, end, reminder
    ))

    conn.commit()
    conn.close()


# ==========================================
# 2. GET TASKS
# ==========================================

def get_tasks(task_date):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM tasks
        WHERE task_date = ?
        ORDER BY id DESC
    """, (task_date,))

    tasks = cursor.fetchall()

    conn.close()

    return tasks


# ==========================================
# 3. COMPLETE A TASK
# ==========================================

def complete_task(task_id):

    conn = get_connection()

    conn.execute("""
        UPDATE tasks
        SET completed = 1
        WHERE id = ?
    """, (task_id,))

    conn.commit()
    conn.close()


# ==========================================
# 4. DELETE A TASK
# ==========================================

def delete_task(task_id):

    conn = get_connection()

    conn.execute("""
        DELETE FROM tasks
        WHERE id = ?
    """, (task_id,))

    conn.commit()
    conn.close()


# ==========================================
# 5. START TIMER
# ==========================================

def start_timer(task_id):

    conn = get_connection()

    now = datetime.now(timezone.utc).isoformat()

    conn.execute("""
        UPDATE tasks
        SET timer_started_at = ?
        WHERE id = ?
        AND timer_started_at IS NULL
    """, (now, task_id))

    conn.commit()
    conn.close()


# ==========================================
# 6. STOP TIMER
# ==========================================

def stop_timer(task_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT timer_started_at, duration_seconds
        FROM tasks
        WHERE id = ?
    """, (task_id,))

    result = cursor.fetchone()

    if result and result[0]:

        started = datetime.fromisoformat(result[0])

        elapsed = int(
            (datetime.now(timezone.utc) - started).total_seconds()
        )

        total = (result[1] or 0) + elapsed

        cursor.execute("""
            UPDATE tasks
            SET duration_seconds = ?,
                timer_started_at = NULL
            WHERE id = ?
        """, (total, task_id))

    conn.commit()
    conn.close()


# ==========================================
# 7. ADD PAST COMPLETED ACTIVITY
# ==========================================

def add_completed_task(
    name, category, activity_date, start, end
):

    start_dt = datetime.combine(activity_date, start)
    end_dt = datetime.combine(activity_date, end)

    duration = int(
        (end_dt - start_dt).total_seconds()
    )

    if duration <= 0:
        raise ValueError("End time must be after start time.")

    conn = get_connection()

    conn.execute("""
        INSERT INTO tasks (
            task_name,
            category,
            task_date,
            start_time,
            end_time,
            duration_seconds,
            completed,
            reminder_at,
            reminder_sent,
            timer_started_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 1, NULL, 0, NULL)
    """, (
        name,
        category,
        activity_date.isoformat(),
        start.strftime("%H:%M"),
        end.strftime("%H:%M"),
        duration
    ))

    conn.commit()
    conn.close()


# ==========================================
# 8. GET FIXED DAILY ACTIVITIES
# ==========================================

def get_daily_activities(activity_date):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            a.id,
            a.activity_name,
            a.category,
            COALESCE(l.completed, 0)

        FROM daily_activities a

        LEFT JOIN daily_activity_logs l
            ON a.id = l.activity_id
            AND l.activity_date = ?

        WHERE a.active = 1

        ORDER BY
            CASE
                WHEN a.activity_name = 'Wake up early' THEN 1
                WHEN a.activity_name = 'Morning Run' THEN 2
                ELSE 3
            END,
            a.id
    """, (activity_date,))

    activities = cursor.fetchall()

    conn.close()

    return activities


# ==========================================
# 9. UPDATE DAILY CHECKBOX
# ==========================================

def update_daily_activity(
    activity_id, activity_date, completed
):

    conn = get_connection()

    completed_at = (
        datetime.now().isoformat(timespec="seconds")
        if completed else None
    )

    conn.execute("""
        INSERT INTO daily_activity_logs
        (activity_id, activity_date, completed, completed_at)

        VALUES (?, ?, ?, ?)

        ON CONFLICT(activity_id, activity_date)

        DO UPDATE SET
            completed = excluded.completed,
            completed_at = excluded.completed_at
    """, (
        activity_id,
        activity_date,
        int(completed),
        completed_at
    ))

    conn.commit()
    conn.close()


# ==========================================
# 10. DAILY PROGRESS
# ==========================================

def get_daily_progress(activity_date):

    activities = get_daily_activities(activity_date)

    total = len(activities)

    completed = sum(
        activity[3] for activity in activities
    )

    percentage = (
        completed / total * 100 if total else 0
    )

    return total, completed, percentage


# ==========================================
# 11. PRODUCTIVITY STREAK
# ==========================================

def get_streak():

    conn = get_connection()

    cursor = conn.cursor()

    # Combine manual tasks and fixed checklist.
    # UNION prevents duplicate dates.

    cursor.execute("""
        SELECT task_date AS activity_date
        FROM tasks
        WHERE completed = 1

        UNION

        SELECT activity_date
        FROM daily_activity_logs
        WHERE completed = 1

        ORDER BY activity_date DESC
    """)

    dates = {
        date.fromisoformat(row[0])
        for row in cursor.fetchall()
    }

    conn.close()

    today = date.today()

    # Allow today's activities to remain incomplete
    # without immediately breaking yesterday's streak.

    current = (
        today if today in dates
        else today - timedelta(days=1)
    )

    streak = 0

    while current in dates:

        streak += 1

        current -= timedelta(days=1)

    return streak

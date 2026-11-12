
import streamlit as st
import pandas as pd
import plotly.express as px
from tracker import get_streak

from datetime import date, datetime, time, timedelta

from database import create_table, get_connection
from tracker import (
    add_task,
    add_completed_task,
    get_tasks,
    complete_task,
    delete_task,
    start_timer,
    stop_timer,
    get_streak,
    get_daily_activities,
    update_daily_activity,
    get_daily_progress
)

st.set_page_config(
    page_title="Daily Activity Tracker",
    page_icon="📅",
    layout="wide"
)

create_table()
from reminders import start_reminder_service

start_reminder_service()

st.title("📅 Daily Activity Tracker")
st.caption("Plan your day. Track your progress. Build consistency.")

# Sidebar
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Choose a section",
    [
        "Dashboard",
        "Daily Checklist",
        "Log Past Activities",
        "History",
        "Analytics"
    ]
)

selected_date = st.sidebar.date_input(
    "Select date",
    value=date.today()
)

date_string = selected_date.isoformat()

# Get today's tasks
tasks = get_tasks(date_string)
st.metric("🔥 Current Streak", f"{get_streak()} days")


if page == "Dashboard":

    st.subheader("Today's Dashboard")

    total = len(tasks)
    completed = sum(task[7] for task in tasks)
    pending = total - completed

    progress = completed / total if total else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tasks", total)
    col2.metric("Completed", completed)
    col3.metric("Pending", pending)
    col4.metric("🔥 Streak", f"{get_streak()} days")
    st.progress(progress)
    st.write(f"Daily Progress: {progress * 100:.1f}%")

    st.divider()

    st.subheader("Add New Activity")

    with st.form("task_form"):

        name = st.text_input("Activity Name")

        category = st.selectbox(
            "Category",
            ["Personal", "Fitness", "Learning",
             "Work", "Projects", "Other"]
        )

        c1, c2 = st.columns(2)

        start = c1.time_input(
            "Planned Start",
            value=time(9, 0)
        )

        end = c2.time_input(
            "Planned End",
            value=time(10, 0)
        )

        reminder_enabled = st.checkbox("Set reminder")

        reminder_time = None

        if reminder_enabled:
            reminder_time = st.time_input(
                "Reminder time",
                value=time(8, 55)
            )

        submitted = st.form_submit_button("Add Activity")

        if submitted:

            if not name.strip():
                st.error("Please enter an activity name.")

            elif end <= start:
                st.error("End time must be after start time.")

            else:
                reminder = (
                    datetime.combine(
                        selected_date, reminder_time
                    ).isoformat()
                    if reminder_enabled else None
                )

                add_task(
                    name.strip(),
                    category,
                    date_string,
                    start.strftime("%H:%M"),
                    end.strftime("%H:%M"),
                    reminder
                )

                st.success("Activity added!")
                st.rerun()

    st.divider()

    st.subheader("Your Activities")

    for task in tasks:

        task_id = task[0]
        task_name = task[1]
        task_category = task[2]
        task_start = task[4]
        task_end = task[5]
        duration = task[6] or 0
        is_completed = task[7]
        timer_started = task[10]

        with st.container(border=True):

            c1, c2, c3 = st.columns([4, 1, 2])

            with c1:
                st.write(
                    f"**{task_name}**"
                )
                st.caption(
                    f"{task_category} | {task_start} - {task_end}"
                )

            with c2:
                st.write(
                    "✅ Completed" if is_completed
                    else "⏳ Pending"
                )

            with c3:

                if not is_completed:

                    if timer_started:
                        if st.button("Stop Timer", key=f"stop{task_id}"):
                            stop_timer(task_id)
                            st.rerun()

                    else:
                        if st.button("Start Timer", key=f"start{task_id}"):
                            start_timer(task_id)
                            st.rerun()

                    if st.button("Complete", key=f"done{task_id}"):
                        if timer_started:
                            stop_timer(task_id)

                        complete_task(task_id)
                        st.rerun()

                if st.button("Delete", key=f"delete{task_id}"):
                    delete_task(task_id)
                    st.rerun()

            hours, remainder = divmod(duration, 3600)
            minutes = remainder // 60

            st.caption(
                f"Time tracked: {hours}h {minutes}m"
            )

elif page == "Daily Checklist":

    st.subheader("📅 My Daily Activities")

    st.write(
        "Complete your regular activities "
        "by checking the boxes."
    )

    activity_date = selected_date.isoformat()

    activities = get_daily_activities(activity_date)

    total, completed, percentage = get_daily_progress(
        activity_date
    )

    # Progress section
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Activities", total)
    col2.metric("Completed", completed)
    col3.metric("Progress", f"{percentage:.1f}%")

    st.progress(percentage / 100)

    st.divider()

    # Display fixed activities
    for activity in activities:

        activity_id = activity[0]
        activity_name = activity[1]
        category = activity[2]
        is_completed = bool(activity[3])

        st.checkbox(
            f"{activity_name} ({category})",
            value=is_completed,
            key=f"daily_{activity_id}_{activity_date}",
            on_change=update_daily_activity,
            args=(
                activity_id,
                activity_date,
                not is_completed
            )
        )

    if completed == total and total > 0:
        st.success("🎉 Congratulations! All activities completed!")

    st.caption(
        "Your progress is automatically saved for the selected date."
    )


elif page == "Log Past Activities":

    st.subheader("📝 Log Previously Completed Activities")

    st.write(
        "Record activities you completed before "
        "starting to use this application."
    )

    with st.form("past_activity_form"):

        name = st.text_input("Activity Name")

        category = st.selectbox(
            "Category",
            [
                "Personal",
                "Fitness",
                "Learning",
                "Work",
                "Projects",
                "Other"
            ],
            key="past_category"
        )

        activity_date = st.date_input(
            "Date Completed",
            value=date.today(),
            max_value=date.today(),
            key="past_date"
        )

        col1, col2 = st.columns(2)

        start = col1.time_input(
            "Start Time",
            value=time(9, 0),
            key="past_start"
        )

        end = col2.time_input(
            "End Time",
            value=time(11, 0),
            key="past_end"
        )

        submitted = st.form_submit_button(
            "Save as Completed",
            type="primary"
        )

        if submitted:

            if not name.strip():
                st.error("Please enter an activity name.")

            elif end <= start:
                st.error("End time must be after start time.")

            else:
                add_completed_task(
                    name.strip(),
                    category,
                    activity_date,
                    start,
                    end
                )

                st.success(
                    f"'{name}' successfully added "
                    f"to completed activities!"
                )

                st.rerun()



elif page == "History":

    st.subheader("Activity History")

    conn = get_connection()

    df = pd.read_sql_query("""
    SELECT
        id,
        task_date,
        task_name,
        category,
        completed,
        duration_seconds
    FROM tasks

    UNION ALL

    SELECT
        l.activity_id AS id,
        l.activity_date AS task_date,
        a.activity_name AS task_name,
        a.category,
        l.completed,
        0 AS duration_seconds
    FROM daily_activity_logs l

    JOIN daily_activities a
        ON l.activity_id = a.id

    ORDER BY task_date DESC
""", conn)


elif page == "Analytics":

    st.subheader("Productivity Analytics")

    conn = get_connection()

    df = pd.read_sql_query(
        "SELECT * FROM tasks",
        conn
    )

    conn.close()

    if not df.empty:

        daily = df.groupby("task_date").agg(
            total=("id", "count"),
            completed=("completed", "sum")
        ).reset_index()

        daily["progress"] = (
            daily["completed"] / daily["total"] * 100
        )

        fig = px.line(
            daily,
            x="task_date",
            y="progress",
            markers=True,
            title="Daily Completion Percentage"
        )

        fig.update_yaxes(range=[0, 100])

        st.plotly_chart(fig, use_container_width=True)

        category = df.groupby("category").agg(
            tasks=("id", "count"),
            completed=("completed", "sum")
        ).reset_index()

        fig2 = px.bar(
            category,
            x="category",
            y="tasks",
            color="category",
            title="Activities by Category"
        )

        st.plotly_chart(fig2, use_container_width=True)

        total_seconds = df["duration_seconds"].sum()

        st.metric(
            "Total Tracked Hours",
            f"{total_seconds / 3600:.2f} hours"
        )

    else:
        st.info("Complete some activities to see analytics.")


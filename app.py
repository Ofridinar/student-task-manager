from flask import Flask, render_template, request, redirect, flash
from datetime import datetime, date
from dotenv import load_dotenv
from email.message import EmailMessage
import smtplib
import os
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = "student_task_manager_secret_key"

TASKS_FILE = "tasks.json"

PRIORITY_ORDER = {
    "High": 1,
    "Medium": 2,
    "Low": 3
}


def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []

    try:
        with open(TASKS_FILE, "r") as file:
            tasks = json.load(file)

        for task in tasks:
            task["due_date"] = datetime.strptime(task["due_date"], "%Y-%m-%d").date()

            # Compatibility with old tasks
            if "priority" not in task:
                task["priority"] = "Medium"

            if "email_sent" not in task:
                task["email_sent"] = False

            if "completed" not in task:
                task["completed"] = False

        return tasks

    except json.JSONDecodeError:
        return []


def save_tasks():
    tasks_to_save = []

    for task in tasks:
        tasks_to_save.append({
            "title": task["title"],
            "due_date": task["due_date"].strftime("%Y-%m-%d"),
            "priority": task["priority"],
            "completed": task["completed"],
            "email_sent": task["email_sent"]
        })

    with open(TASKS_FILE, "w") as file:
        json.dump(tasks_to_save, file, indent=4)


tasks = load_tasks()


def send_email_notification(task_title, due_date):
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")
    receiver_email = os.getenv("RECEIVER_EMAIL")

    if not sender_email or not sender_password or not receiver_email:
        print("Email settings are missing in .env file.")
        return False

    message = EmailMessage()
    message["Subject"] = "Task Reminder - Due Today"
    message["From"] = sender_email
    message["To"] = receiver_email

    message.set_content(
        f"""
Hello,

This is a reminder that your task is due today.

Task: {task_title}
Due date: {due_date}

Good luck!
"""
    )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(message)

        print(f"Email sent for task: {task_title}")
        return True

    except Exception as error:
        print(f"Failed to send email: {error}")
        return False


def validate_due_date(due_date_input):
    today = date.today()
    max_year = today.year + 5

    try:
        due_date = datetime.strptime(due_date_input, "%Y-%m-%d").date()
    except ValueError:
        return None, "Invalid date. Please enter a real date in YYYY-MM-DD format."

    if due_date.year < today.year:
        return None, "Invalid year. The year cannot be in the past."

    if due_date.year > max_year:
        return None, f"Invalid year. Please enter a year between {today.year} and {max_year}."

    if due_date < today:
        return None, "Invalid date. The due date cannot be in the past."

    return due_date, None


def validate_priority(priority):
    if priority not in PRIORITY_ORDER:
        return "Medium"

    return priority


def update_task_statuses_and_send_emails():
    today = date.today()
    changed = False

    for task in tasks:
        if task["completed"]:
            task["status"] = "Completed"

        elif task["due_date"] < today:
            task["status"] = "Overdue"

        elif task["due_date"] == today:
            task["status"] = "Due Today"

            if not task["email_sent"]:
                email_was_sent = send_email_notification(
                    task["title"],
                    task["due_date"]
                )

                if email_was_sent:
                    task["email_sent"] = True
                    changed = True

        else:
            task["status"] = "On Time"

    if changed:
        save_tasks()


def get_sorted_tasks(task_list):
    return sorted(
        task_list,
        key=lambda task: (
            task["completed"],
            task["due_date"],
            PRIORITY_ORDER.get(task["priority"], 2)
        )
    )


@app.route("/")
def home():
    update_task_statuses_and_send_emails()

    search_query = request.args.get("search", "").strip().lower()

    if search_query:
        filtered_tasks = [
            task for task in tasks
            if search_query in task["title"].lower()
        ]
    else:
        filtered_tasks = tasks

    sorted_tasks = get_sorted_tasks(filtered_tasks)

    return render_template(
        "index.html",
        tasks=sorted_tasks,
        search_query=search_query
    )


@app.route("/add", methods=["POST"])
def add_task():
    title = request.form["title"].strip()
    due_date_input = request.form["due_date"]
    priority = validate_priority(request.form["priority"])

    if not title:
        flash("Task title cannot be empty.")
        return redirect("/")

    due_date, error_message = validate_due_date(due_date_input)

    if error_message:
        flash(error_message)
        return redirect("/")

    task = {
        "title": title,
        "due_date": due_date,
        "priority": priority,
        "completed": False,
        "email_sent": False
    }

    tasks.append(task)
    save_tasks()

    flash("Task added successfully!")
    return redirect("/")


@app.route("/complete/<int:task_index>")
def complete_task(task_index):
    if 0 <= task_index < len(tasks):
        tasks[task_index]["completed"] = True
        save_tasks()
        flash("Task marked as completed.")
    else:
        flash("Invalid task number.")

    return redirect("/")


@app.route("/delete/<int:task_index>")
def delete_task(task_index):
    if 0 <= task_index < len(tasks):
        tasks.pop(task_index)
        save_tasks()
        flash("Task deleted.")
    else:
        flash("Invalid task number.")

    return redirect("/")


@app.route("/edit/<int:task_index>")
def edit_task_page(task_index):
    if 0 <= task_index < len(tasks):
        return render_template(
            "index.html",
            tasks=get_sorted_tasks(tasks),
            edit_task=tasks[task_index],
            edit_index=task_index,
            search_query=""
        )

    flash("Invalid task number.")
    return redirect("/")


@app.route("/update/<int:task_index>", methods=["POST"])
def update_task(task_index):
    if not (0 <= task_index < len(tasks)):
        flash("Invalid task number.")
        return redirect("/")

    title = request.form["title"].strip()
    due_date_input = request.form["due_date"]
    priority = validate_priority(request.form["priority"])

    if not title:
        flash("Task title cannot be empty.")
        return redirect(f"/edit/{task_index}")

    due_date, error_message = validate_due_date(due_date_input)

    if error_message:
        flash(error_message)
        return redirect(f"/edit/{task_index}")

    old_due_date = tasks[task_index]["due_date"]

    tasks[task_index]["title"] = title
    tasks[task_index]["due_date"] = due_date
    tasks[task_index]["priority"] = priority

    # If the date changed, allow a new email reminder
    if old_due_date != due_date:
        tasks[task_index]["email_sent"] = False

    save_tasks()

    flash("Task updated successfully!")
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
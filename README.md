# Student Task Manager

A simple Flask web application for managing student tasks, deadlines, priorities, and email reminders.

## Features

- Add new tasks
- Set due dates
- Validate dates
- Mark tasks as completed
- Delete tasks
- Edit tasks
- Search tasks
- Sort tasks by due date and priority
- Save tasks to JSON
- Send email reminders for tasks due today

## Technologies

- Python
- Flask
- HTML
- CSS
- JSON
- SMTP email notifications

## How to Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file:

```env
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
RECEIVER_EMAIL=your_email@gmail.com
```

3. Run the app:

```bash
python app.py
```

4. Open in browser:

```text
http://127.0.0.1:5000
```

## Screenshot

![App Screenshot](student-task-manager.png)

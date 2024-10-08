# FastAPI Attendance Management System

This project is a simple attendance management system built with FastAPI and SQLAlchemy. It allows users to sign up, sign in, punch in and out for work, and view their monthly attendance records. Admins can view all users' attendance records.

## Features

- User registration and login
- Punch-in and punch-out functionality
- View daily and monthly attendance
- Admin view for all users' attendance

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Git repo link:

https://github.com/atulsingh9507/attendance_app



1. **Create a virtual environment (optional but recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

2. **Install the dependencies:**

    pip install -r requirements.txt
    ```

3. **Run the application:**

    uvicorn main:app --reload
    ```

    This will start the FastAPI server at `http://127.0.0.1:8000`.


## Acknowledgements

- FastAPI: A modern, fast (high-performance) web framework for building APIs with Python 3.7+.
- SQLAlchemy: The Python SQL toolkit and Object Relational Mapper (ORM).
- Uvicorn: A lightning-fast ASGI server.


"""
database.py
====================================================================
Database Connectivity & Lifecycle Management
Provides secure, parameterized connections to MySQL and schema init.
====================================================================
"""

import os
from typing import Optional, Tuple, Any
import mysql.connector
from mysql.connector import errorcode, Error
from dotenv import load_dotenv

# Load environment variables from .env file located in project directory
load_dotenv()


def get_db_config(use_database: bool = True) -> dict:
    """
    Retrieve database configuration dictionary from environment variables.
    Safe defaults are provided for beginner local setup.
    """
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "charset": "utf8mb4",
        "use_pure": True,
    }
    if use_database:
        config["database"] = os.getenv("DB_NAME", "student_performance_db")
    return config


def get_db_connection(use_database: bool = True):
    """
    Create and return an active MySQL connection.
    Raises ConnectionError with beginner-friendly diagnostics on failure.
    Never exposes passwords in logs or error messages.
    """
    config = get_db_config(use_database=use_database)
    db_target = config.get("database", "MySQL Server")
    host = config["host"]
    port = config["port"]
    user = config["user"]

    try:
        conn = mysql.connector.connect(**config)
        return conn
    except Error as err:
        if err.errno == errorcode.CR_CONN_HOST_ERROR or err.errno == 2003:
            raise ConnectionError(
                f"Could not connect to MySQL server at {host}:{port}. "
                f"Please ensure the MySQL service (e.g., MySQL80) is started."
            ) from err
        elif err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            raise ConnectionError(
                f"Access denied for user '{user}' at {host}:{port}. "
                f"Please verify your DB_USER and DB_PASSWORD in the .env file."
            ) from err
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            raise ConnectionError(
                f"Database '{db_target}' does not exist on {host}:{port}. "
                f"Please initialize the database first using the Setup button or database.sql."
            ) from err
        else:
            raise ConnectionError(
                f"MySQL Connection Error (Code {err.errno}): {err.msg}"
            ) from err


def test_db_connection() -> Tuple[bool, str]:
    """
    Test whether MySQL server and the target database are reachable.
    Returns (True, success_message) or (False, detailed_error_message).
    """
    try:
        conn = get_db_connection(use_database=True)
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE(), VERSION();")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        db_name, version = row if row else ("Unknown", "Unknown")
        return True, f"Connected successfully to MySQL ({version}) on database '{db_name}'."
    except Exception as exc:
        return False, str(exc)


def init_db() -> Tuple[bool, str]:
    """
    Initialize the database and tables according to schema.
    Creates 'student_performance_db' and required tables with all constraints.
    """
    db_name = os.getenv("DB_NAME", "student_performance_db")
    
    # Step 1: Connect to server without database to create DB if needed
    try:
        server_conn = get_db_connection(use_database=False)
        server_cur = server_conn.cursor()
        server_cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        )
        server_cur.close()
        server_conn.close()
    except Exception as exc:
        return False, f"Failed to create database '{db_name}': {exc}"

    # Step 2: Connect to the specific database and create tables
    try:
        conn = get_db_connection(use_database=True)
        cur = conn.cursor()

        # Table: students
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id INT AUTO_INCREMENT PRIMARY KEY,
                roll_no VARCHAR(50) NOT NULL UNIQUE,
                name VARCHAR(100) NOT NULL,
                section VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT chk_roll_no_not_empty CHECK (LENGTH(TRIM(roll_no)) > 0),
                CONSTRAINT chk_student_name_not_empty CHECK (LENGTH(TRIM(name)) > 0),
                CONSTRAINT chk_section_not_empty CHECK (LENGTH(TRIM(section)) > 0)
            ) ENGINE=InnoDB;
        """)

        # Table: subjects
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id INT AUTO_INCREMENT PRIMARY KEY,
                subject_name VARCHAR(100) NOT NULL UNIQUE,
                max_marks DECIMAL(5,2) NOT NULL,
                pass_marks DECIMAL(5,2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT chk_subject_name_not_empty CHECK (LENGTH(TRIM(subject_name)) > 0),
                CONSTRAINT chk_max_marks_positive CHECK (max_marks > 0),
                CONSTRAINT chk_pass_marks_valid CHECK (pass_marks > 0 AND pass_marks <= max_marks)
            ) ENGINE=InnoDB;
        """)

        # Table: marks
        cur.execute("""
            CREATE TABLE IF NOT EXISTS marks (
                mark_id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                subject_id INT NOT NULL,
                assessment VARCHAR(50) NOT NULL,
                marks_obtained DECIMAL(5,2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT chk_marks_obtained_non_negative CHECK (marks_obtained >= 0),
                CONSTRAINT chk_assessment_not_empty CHECK (LENGTH(TRIM(assessment)) > 0),
                CONSTRAINT fk_marks_student FOREIGN KEY (student_id)
                    REFERENCES students(student_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                CONSTRAINT fk_marks_subject FOREIGN KEY (subject_id)
                    REFERENCES subjects(subject_id)
                    ON DELETE RESTRICT
                    ON UPDATE CASCADE,
                CONSTRAINT uq_student_subject_assessment UNIQUE (student_id, subject_id, assessment)
            ) ENGINE=InnoDB;
        """)

        # Safely create indexes if they don't already exist
        for index_sql in [
            "CREATE INDEX idx_marks_student ON marks(student_id);",
            "CREATE INDEX idx_marks_subject ON marks(subject_id);",
            "CREATE INDEX idx_marks_assessment ON marks(assessment);"
        ]:
            try:
                cur.execute(index_sql)
            except Error:
                pass  # Index already exists

        conn.commit()
        cur.close()
        conn.close()
        return True, f"Database '{db_name}' and all tables initialized successfully."
    except Exception as exc:
        return False, f"Failed to initialize tables: {exc}"


def load_sample_data() -> Tuple[bool, str]:
    """
    Populate database with fictional students, subjects, and test marks.
    Safe to execute multiple times (prevents duplicates).
    """
    try:
        conn = get_db_connection(use_database=True)
        cur = conn.cursor()

        # 1. Sample subjects
        sample_subjects = [
            ("Mathematics", 100.0, 40.0),
            ("Python Programming", 100.0, 40.0),
            ("Digital Logic Design", 100.0, 40.0),
        ]
        for name, max_m, pass_m in sample_subjects:
            cur.execute("""
                INSERT INTO subjects (subject_name, max_marks, pass_marks)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE max_marks=%s, pass_marks=%s
            """, (name, max_m, pass_m, max_m, pass_m))

        # 2. Sample students (fictional)
        sample_students = [
            ("101", "Arun Kumar", "A"),
            ("102", "Priya Sharma", "A"),
            ("103", "Rahul Verma", "B"),
            ("104", "Sneha Reddy", "B"),
            ("105", "Kiran Das", "A"),
        ]
        for roll, name, sec in sample_students:
            cur.execute("""
                INSERT INTO students (roll_no, name, section)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE name=%s, section=%s
            """, (roll, name, sec, name, sec))

        conn.commit()

        # Retrieve student IDs and subject IDs
        cur.execute("SELECT roll_no, student_id FROM students")
        student_map = dict(cur.fetchall())

        cur.execute("SELECT subject_name, subject_id FROM subjects")
        subject_map = dict(cur.fetchall())

        # 3. Sample marks (assessment: 'Final Exam')
        # - Arun Kumar (101): Topper 1 (95 + 92 + 90 = 277)
        # - Priya Sharma (102): Equal score tie (90 + 95 + 92 = 277)
        # - Rahul Verma (103): Fails Math (35 < 40)
        # - Sneha Reddy (104): Support needed (42 + 45 + 44 = 131/300 = 43.67% < 50%)
        # - Kiran Das (105): Missing marks (only Math: 80)
        sample_marks = [
            ("101", "Mathematics", "Final Exam", 95.0),
            ("101", "Python Programming", "Final Exam", 92.0),
            ("101", "Digital Logic Design", "Final Exam", 90.0),
            ("102", "Mathematics", "Final Exam", 90.0),
            ("102", "Python Programming", "Final Exam", 95.0),
            ("102", "Digital Logic Design", "Final Exam", 92.0),
            ("103", "Mathematics", "Final Exam", 35.0),
            ("103", "Python Programming", "Final Exam", 75.0),
            ("103", "Digital Logic Design", "Final Exam", 65.0),
            ("104", "Mathematics", "Final Exam", 42.0),
            ("104", "Python Programming", "Final Exam", 45.0),
            ("104", "Digital Logic Design", "Final Exam", 44.0),
            ("105", "Mathematics", "Final Exam", 80.0),
        ]

        for roll, sub_name, assessment, mark_val in sample_marks:
            s_id = student_map.get(roll)
            sub_id = subject_map.get(sub_name)
            if s_id and sub_id:
                cur.execute("""
                    INSERT INTO marks (student_id, subject_id, assessment, marks_obtained)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE marks_obtained=%s
                """, (s_id, sub_id, assessment, mark_val, mark_val))

        conn.commit()
        cur.close()
        conn.close()
        return True, "Fictional sample data loaded successfully with 5 students, 3 subjects, and test marks."
    except Exception as exc:
        return False, f"Error loading sample data: {exc}"

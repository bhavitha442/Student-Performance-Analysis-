"""
student_operations.py
====================================================================
Student Management Operations
Validation, CRUD actions, and search utilities for student records.
====================================================================
"""

from typing import List, Dict, Any, Tuple, Optional
from mysql.connector import Error, errorcode
from database import get_db_connection


def validate_student_data(roll_no: Any, name: Any, section: Any) -> Tuple[bool, str]:
    """
    Validate student input fields before performing database operations.
    Pure validation function (can be tested independently without MySQL).
    """
    if roll_no is None or str(roll_no).strip() == "":
        return False, "Roll number is required and cannot be blank."
    if name is None or str(name).strip() == "":
        return False, "Student name is required and cannot be blank."
    if section is None or str(section).strip() == "":
        return False, "Section is required and cannot be blank."
    
    clean_roll = str(roll_no).strip()
    clean_name = str(name).strip()
    clean_sec = str(section).strip()

    if len(clean_roll) > 50:
        return False, "Roll number must not exceed 50 characters."
    if len(clean_name) > 100:
        return False, "Student name must not exceed 100 characters."
    if len(clean_sec) > 20:
        return False, "Section must not exceed 20 characters."

    return True, ""


def add_student(roll_no: str, name: str, section: str) -> Tuple[bool, str, Optional[int]]:
    """
    Add a new student to the database.
    Rejects blank fields and duplicate roll numbers.
    """
    is_valid, err_msg = validate_student_data(roll_no, name, section)
    if not is_valid:
        return False, err_msg, None

    clean_roll = str(roll_no).strip()
    clean_name = str(name).strip()
    clean_sec = str(section).strip().upper()

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check for duplicate roll number beforehand
        cur.execute("SELECT student_id FROM students WHERE roll_no = %s", (clean_roll,))
        existing = cur.fetchone()
        if existing:
            cur.close()
            conn.close()
            return False, f"A student with Roll Number '{clean_roll}' already exists.", None

        # Insert new record using parameterized query
        cur.execute(
            "INSERT INTO students (roll_no, name, section) VALUES (%s, %s, %s)",
            (clean_roll, clean_name, clean_sec)
        )
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
        conn.close()
        return True, f"Student '{clean_name}' (Roll No: {clean_roll}) added successfully.", new_id
    except ConnectionError as ce:
        return False, str(ce), None
    except Error as err:
        if err.errno == errorcode.ER_DUP_ENTRY:
            return False, f"Duplicate roll number '{clean_roll}' is not allowed.", None
        return False, f"Database error while adding student: {err.msg}", None


def get_all_students() -> List[Dict[str, Any]]:
    """
    Retrieve all students ordered by roll number.
    Returns a list of dictionaries.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT student_id, roll_no, name, section, created_at FROM students ORDER BY roll_no ASC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception:
        return []


def get_student_by_id(student_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single student record by primary key ID.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT student_id, roll_no, name, section FROM students WHERE student_id = %s", (student_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row
    except Exception:
        return None


def search_students(query: str) -> List[Dict[str, Any]]:
    """
    Search students by roll number or name (case-insensitive substring match).
    """
    clean_query = str(query).strip()
    if not clean_query:
        return get_all_students()

    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        param = f"%{clean_query}%"
        cur.execute(
            "SELECT student_id, roll_no, name, section FROM students "
            "WHERE roll_no LIKE %s OR name LIKE %s ORDER BY roll_no ASC",
            (param, param)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception:
        return []


def update_student(student_id: int, roll_no: str, name: str, section: str) -> Tuple[bool, str]:
    """
    Update student name, roll number, and section.
    Rejects duplicate roll numbers across other students.
    """
    is_valid, err_msg = validate_student_data(roll_no, name, section)
    if not is_valid:
        return False, err_msg

    clean_roll = str(roll_no).strip()
    clean_name = str(name).strip()
    clean_sec = str(section).strip().upper()

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if roll number is already taken by another student
        cur.execute(
            "SELECT student_id FROM students WHERE roll_no = %s AND student_id != %s",
            (clean_roll, student_id)
        )
        if cur.fetchone():
            cur.close()
            conn.close()
            return False, f"Roll Number '{clean_roll}' is already assigned to another student."

        cur.execute(
            "UPDATE students SET roll_no = %s, name = %s, section = %s WHERE student_id = %s",
            (clean_roll, clean_name, clean_sec, student_id)
        )
        conn.commit()
        affected = cur.rowcount
        cur.close()
        conn.close()

        if affected == 0:
            return True, "No changes were made or student not found."
        return True, f"Student '{clean_name}' updated successfully."
    except ConnectionError as ce:
        return False, str(ce)
    except Error as err:
        return False, f"Database error updating student: {err.msg}"


def delete_student(student_id: int) -> Tuple[bool, str]:
    """
    Delete a student record.
    Foreign key ON DELETE CASCADE will remove associated marks cleanly.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name, roll_no FROM students WHERE student_id = %s", (student_id,))
        student = cur.fetchone()
        if not student:
            cur.close()
            conn.close()
            return False, "Student not found."

        cur.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True, f"Student '{student[0]}' (Roll: {student[1]}) and all related records deleted successfully."
    except ConnectionError as ce:
        return False, str(ce)
    except Error as err:
        return False, f"Database error deleting student: {err.msg}"

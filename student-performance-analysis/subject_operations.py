"""
subject_operations.py
====================================================================
Subject Management Operations
Validation, CRUD actions, and consistency checks for subjects.
====================================================================
"""

from typing import List, Dict, Any, Tuple, Optional
from mysql.connector import Error, errorcode
from database import get_db_connection


def validate_subject_data(subject_name: Any, max_marks: Any, pass_marks: Any) -> Tuple[bool, str, float, float]:
    """
    Validate subject input parameters.
    - subject_name must not be empty.
    - max_marks must be a positive float (> 0).
    - pass_marks must be > 0 and <= max_marks.
    Returns: (is_valid, error_message, parsed_max_marks, parsed_pass_marks)
    """
    if subject_name is None or str(subject_name).strip() == "":
        return False, "Subject name cannot be empty.", 0.0, 0.0

    clean_name = str(subject_name).strip()
    if len(clean_name) > 100:
        return False, "Subject name must not exceed 100 characters.", 0.0, 0.0

    try:
        max_m = float(max_marks)
    except (ValueError, TypeError):
        return False, "Maximum marks must be a valid number.", 0.0, 0.0

    try:
        pass_m = float(pass_marks)
    except (ValueError, TypeError):
        return False, "Pass marks must be a valid number.", 0.0, 0.0

    if max_m <= 0:
        return False, "Maximum marks must be greater than zero.", 0.0, 0.0

    if pass_m <= 0:
        return False, "Pass marks must be greater than zero.", 0.0, 0.0

    if pass_m > max_m:
        return False, f"Pass marks ({pass_m}) cannot exceed maximum marks ({max_m}).", 0.0, 0.0

    return True, "", round(max_m, 2), round(pass_m, 2)


def add_subject(subject_name: str, max_marks: float, pass_marks: float) -> Tuple[bool, str, Optional[int]]:
    """
    Add a new subject to the database.
    Rejects invalid marks bounds and duplicate names.
    """
    is_valid, err_msg, max_m, pass_m = validate_subject_data(subject_name, max_marks, pass_marks)
    if not is_valid:
        return False, err_msg, None

    clean_name = str(subject_name).strip()

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check for duplicate subject name
        cur.execute("SELECT subject_id FROM subjects WHERE LOWER(subject_name) = LOWER(%s)", (clean_name,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return False, f"A subject with the name '{clean_name}' already exists.", None

        cur.execute(
            "INSERT INTO subjects (subject_name, max_marks, pass_marks) VALUES (%s, %s, %s)",
            (clean_name, max_m, pass_m)
        )
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
        conn.close()
        return True, f"Subject '{clean_name}' added successfully.", new_id
    except ConnectionError as ce:
        return False, str(ce), None
    except Error as err:
        if err.errno == errorcode.ER_DUP_ENTRY:
            return False, f"Subject '{clean_name}' already exists.", None
        return False, f"Database error adding subject: {err.msg}", None


def get_all_subjects() -> List[Dict[str, Any]]:
    """
    Retrieve all subjects ordered alphabetically.
    Returns list of dictionaries.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT subject_id, subject_name, max_marks, pass_marks, created_at FROM subjects ORDER BY subject_name ASC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        # Ensure float types for JSON / Streamlit display
        for row in rows:
            row["max_marks"] = float(row["max_marks"])
            row["pass_marks"] = float(row["pass_marks"])
        return rows
    except Exception:
        return []


def get_subject_by_id(subject_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve subject details by ID.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT subject_id, subject_name, max_marks, pass_marks FROM subjects WHERE subject_id = %s", (subject_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            row["max_marks"] = float(row["max_marks"])
            row["pass_marks"] = float(row["pass_marks"])
        return row
    except Exception:
        return None


def update_subject(subject_id: int, subject_name: str, max_marks: float, pass_marks: float) -> Tuple[bool, str]:
    """
    Update subject parameters.
    Checks that the new max_marks is not lower than any existing marks obtained in this subject.
    """
    is_valid, err_msg, max_m, pass_m = validate_subject_data(subject_name, max_marks, pass_marks)
    if not is_valid:
        return False, err_msg

    clean_name = str(subject_name).strip()

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check duplicate name with another subject
        cur.execute(
            "SELECT subject_id FROM subjects WHERE LOWER(subject_name) = LOWER(%s) AND subject_id != %s",
            (clean_name, subject_id)
        )
        if cur.fetchone():
            cur.close()
            conn.close()
            return False, f"Another subject with the name '{clean_name}' already exists."

        # Check if any existing marks in this subject exceed the proposed new max_marks
        cur.execute(
            "SELECT MAX(marks_obtained) FROM marks WHERE subject_id = %s",
            (subject_id,)
        )
        highest_recorded = cur.fetchone()[0]
        if highest_recorded is not None and float(highest_recorded) > max_m:
            cur.close()
            conn.close()
            return False, (
                f"Cannot reduce maximum marks to {max_m} because an existing marks record "
                f"has {float(highest_recorded)} marks. Please adjust marks records first."
            )

        cur.execute(
            "UPDATE subjects SET subject_name = %s, max_marks = %s, pass_marks = %s WHERE subject_id = %s",
            (clean_name, max_m, pass_m, subject_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return True, f"Subject '{clean_name}' updated successfully."
    except ConnectionError as ce:
        return False, str(ce)
    except Error as err:
        return False, f"Database error updating subject: {err.msg}"


def delete_subject(subject_id: int) -> Tuple[bool, str]:
    """
    Delete a subject after confirmation.
    Rejects deletion if there are existing marks recorded for this subject,
    preventing orphaned or corrupted records.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if any marks exist for this subject
        cur.execute("SELECT COUNT(*) FROM marks WHERE subject_id = %s", (subject_id,))
        marks_count = cur.fetchone()[0]
        if marks_count > 0:
            cur.close()
            conn.close()
            return False, (
                f"Cannot delete subject: {marks_count} marks entry/entries reference this subject. "
                f"Please delete or reassign those marks records first."
            )

        cur.execute("DELETE FROM subjects WHERE subject_id = %s", (subject_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True, "Subject deleted successfully."
    except ConnectionError as ce:
        return False, str(ce)
    except Error as err:
        return False, f"Database error deleting subject: {err.msg}"

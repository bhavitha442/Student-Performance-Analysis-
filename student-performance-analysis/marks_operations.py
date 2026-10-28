"""
marks_operations.py
====================================================================
Marks Management Operations
Validation, CRUD actions, and consistency checks for marks entries.
====================================================================
"""

from typing import List, Dict, Any, Tuple, Optional
from mysql.connector import Error, errorcode
from database import get_db_connection


def validate_marks_data(
    student_id: Any,
    subject_id: Any,
    assessment: Any,
    marks_obtained: Any,
    max_marks: Optional[float] = None
) -> Tuple[bool, str, float]:
    """
    Validate marks parameters:
    - student_id & subject_id must be valid integers.
    - assessment name cannot be empty.
    - marks_obtained must be a valid numeric >= 0.
    - If max_marks is provided, marks_obtained cannot exceed max_marks.
    Returns: (is_valid, error_message, parsed_marks_obtained)
    """
    if student_id is None or str(student_id).strip() == "":
        return False, "Student selection is required.", 0.0

    if subject_id is None or str(subject_id).strip() == "":
        return False, "Subject selection is required.", 0.0

    if assessment is None or str(assessment).strip() == "":
        return False, "Assessment name is required (e.g., 'Midterm 1', 'Final Exam').", 0.0

    clean_assessment = str(assessment).strip()
    if len(clean_assessment) > 50:
        return False, "Assessment name cannot exceed 50 characters.", 0.0

    try:
        val = float(marks_obtained)
    except (ValueError, TypeError):
        return False, "Marks obtained must be a valid number.", 0.0

    if val < 0:
        return False, f"Marks obtained ({val}) cannot be negative.", 0.0

    if max_marks is not None and val > max_marks:
        return False, f"Marks obtained ({val}) cannot exceed the subject maximum marks ({max_marks}).", 0.0

    return True, "", round(val, 2)


def add_mark(
    student_id: int,
    subject_id: int,
    assessment: str,
    marks_obtained: float
) -> Tuple[bool, str, Optional[int]]:
    """
    Insert a new mark record.
    Checks that the student and subject exist, validates against maximum marks,
    and prevents duplicate entries for (student_id, subject_id, assessment).
    If duplicate exists, informs user to edit existing record instead.
    """
    clean_assessment = str(assessment).strip()

    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # Retrieve subject max_marks
        cur.execute("SELECT subject_name, max_marks FROM subjects WHERE subject_id = %s", (subject_id,))
        subject = cur.fetchone()
        if not subject:
            cur.close()
            conn.close()
            return False, "Selected subject does not exist.", None

        max_m = float(subject["max_marks"])

        # Validate mark bounds
        is_valid, err_msg, parsed_mark = validate_marks_data(
            student_id, subject_id, clean_assessment, marks_obtained, max_m
        )
        if not is_valid:
            cur.close()
            conn.close()
            return False, err_msg, None

        # Check for duplicate entry
        cur.execute(
            "SELECT mark_id, marks_obtained FROM marks "
            "WHERE student_id = %s AND subject_id = %s AND LOWER(assessment) = LOWER(%s)",
            (student_id, subject_id, clean_assessment)
        )
        existing = cur.fetchone()
        if existing:
            cur.close()
            conn.close()
            return False, (
                f"A record already exists for this student in '{subject['subject_name']}' "
                f"for assessment '{clean_assessment}' with marks: {float(existing['marks_obtained'])}. "
                f"Please edit the existing record instead of creating a duplicate."
            ), None

        # Insert record
        cur.execute(
            "INSERT INTO marks (student_id, subject_id, assessment, marks_obtained) VALUES (%s, %s, %s, %s)",
            (student_id, subject_id, clean_assessment, parsed_mark)
        )
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
        conn.close()
        return True, "Marks recorded successfully.", new_id
    except ConnectionError as ce:
        return False, str(ce), None
    except Error as err:
        if err.errno == errorcode.ER_DUP_ENTRY:
            return False, "Duplicate mark entry detected. Please edit the existing record.", None
        return False, f"Database error adding mark: {err.msg}", None


def get_all_marks(assessment_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve all marks with joined student and subject details.
    Optional assessment_filter allows querying specific assessments.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        sql = """
            SELECT
                m.mark_id,
                m.student_id,
                s.roll_no,
                s.name AS student_name,
                s.section,
                m.subject_id,
                sub.subject_name,
                sub.max_marks,
                sub.pass_marks,
                m.assessment,
                m.marks_obtained,
                m.created_at
            FROM marks m
            JOIN students s ON m.student_id = s.student_id
            JOIN subjects sub ON m.subject_id = sub.subject_id
        """
        params = []
        if assessment_filter and assessment_filter.strip():
            sql += " WHERE m.assessment = %s"
            params.append(assessment_filter.strip())

        sql += " ORDER BY s.roll_no ASC, sub.subject_name ASC"
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Format numerical fields
        for row in rows:
            row["max_marks"] = float(row["max_marks"])
            row["pass_marks"] = float(row["pass_marks"])
            row["marks_obtained"] = float(row["marks_obtained"])
        return rows
    except Exception:
        return []


def get_marks_for_student(student_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve all marks for a specific student.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT
                m.mark_id,
                m.student_id,
                sub.subject_id,
                sub.subject_name,
                sub.max_marks,
                sub.pass_marks,
                m.assessment,
                m.marks_obtained,
                m.created_at
            FROM marks m
            JOIN subjects sub ON m.subject_id = sub.subject_id
            WHERE m.student_id = %s
            ORDER BY m.assessment ASC, sub.subject_name ASC
        """, (student_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        for row in rows:
            row["max_marks"] = float(row["max_marks"])
            row["pass_marks"] = float(row["pass_marks"])
            row["marks_obtained"] = float(row["marks_obtained"])
        return rows
    except Exception:
        return []


def update_mark(
    mark_id: int,
    assessment: str,
    marks_obtained: float
) -> Tuple[bool, str]:
    """
    Update assessment name or marks obtained for an existing entry.
    """
    clean_assessment = str(assessment).strip()

    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # Retrieve current record and subject max_marks
        cur.execute("""
            SELECT m.student_id, m.subject_id, sub.max_marks
            FROM marks m
            JOIN subjects sub ON m.subject_id = sub.subject_id
            WHERE m.mark_id = %s
        """, (mark_id,))
        current = cur.fetchone()
        if not current:
            cur.close()
            conn.close()
            return False, "Marks record not found."

        student_id = current["student_id"]
        subject_id = current["subject_id"]
        max_m = float(current["max_marks"])

        is_valid, err_msg, parsed_mark = validate_marks_data(
            student_id, subject_id, clean_assessment, marks_obtained, max_m
        )
        if not is_valid:
            cur.close()
            conn.close()
            return False, err_msg

        # Check unique constraint with other rows
        cur.execute("""
            SELECT mark_id FROM marks
            WHERE student_id = %s AND subject_id = %s AND LOWER(assessment) = LOWER(%s) AND mark_id != %s
        """, (student_id, subject_id, clean_assessment, mark_id))
        if cur.fetchone():
            cur.close()
            conn.close()
            return False, f"Another record already exists for this student and subject with assessment '{clean_assessment}'."

        cur.execute("""
            UPDATE marks
            SET assessment = %s, marks_obtained = %s
            WHERE mark_id = %s
        """, (clean_assessment, parsed_mark, mark_id))
        conn.commit()
        cur.close()
        conn.close()
        return True, "Marks record updated successfully."
    except ConnectionError as ce:
        return False, str(ce)
    except Error as err:
        return False, f"Database error updating marks: {err.msg}"


def delete_mark(mark_id: int) -> Tuple[bool, str]:
    """
    Delete a marks record after confirmation.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM marks WHERE mark_id = %s", (mark_id,))
        conn.commit()
        affected = cur.rowcount
        cur.close()
        conn.close()
        if affected == 0:
            return False, "Record not found or already deleted."
        return True, "Marks record deleted successfully."
    except ConnectionError as ce:
        return False, str(ce)
    except Error as err:
        return False, f"Database error deleting marks: {err.msg}"


def get_distinct_assessments() -> List[str]:
    """
    Retrieve unique assessment names recorded in the system.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT assessment FROM marks ORDER BY assessment ASC")
        rows = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows
    except Exception:
        return []

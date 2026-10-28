"""
analysis.py
====================================================================
Academic Performance Analysis Engine
Provides calculations, grading rules, ranking, and aggregated reports.
====================================================================
"""

from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np


# Configurable Grade Thresholds (Percentage)
GRADE_THRESHOLDS = [
    (90.0, "A"),
    (80.0, "B"),
    (70.0, "C"),
    (60.0, "D"),
    (50.0, "E"),
    (0.0,  "F")
]

DEFAULT_SUPPORT_THRESHOLD = 50.0


def calculate_grade(percentage: Optional[float]) -> str:
    """
    Determine letter grade based on percentage:
    A: 90% to 100%
    B: 80% to < 90%
    C: 70% to < 80%
    D: 60% to < 70%
    E: 50% to < 60%
    F: below 50%
    Returns 'N/A' if percentage is None or NaN.
    """
    if percentage is None or pd.isna(percentage):
        return "N/A"
    
    # Cap percentage within realistic range for grade assignment
    p = round(float(percentage), 2)
    for min_score, grade_letter in GRADE_THRESHOLDS:
        if p >= min_score:
            return grade_letter
    return "F"


def compute_student_summary(
    student: Dict[str, Any],
    student_marks: List[Dict[str, Any]],
    all_subjects: List[Dict[str, Any]],
    assessment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate totals, percentage, grade, and pass/fail status for one student.
    
    Academic Rules:
    - A subject is PASSED if marks_obtained >= pass_marks.
    - Overall result is PASS only when EVERY required subject has been passed.
    - If required subjects have missing marks, result is 'Incomplete'.
    - If there are zero marks records, displays 'No marks available'.
    - Assessment handling:
      Filters marks to the specified assessment (e.g. 'Final Exam').
      If assessment is None, considers the primary or latest assessment entry per subject
      to prevent summing repeated assessments together and exceeding maximum marks.
    """
    total_subjects_count = len(all_subjects)
    
    # Filter marks by assessment if specified
    relevant_marks = student_marks
    if assessment and assessment != "All / Primary":
        relevant_marks = [m for m in student_marks if m.get("assessment") == assessment]
    else:
        # If no specific assessment is selected, take one record per subject (latest)
        subject_seen = {}
        for m in sorted(student_marks, key=lambda x: str(x.get("created_at", "")), reverse=True):
            sub_id = m.get("subject_id")
            if sub_id not in subject_seen:
                subject_seen[sub_id] = m
        relevant_marks = list(subject_seen.values())

    if not relevant_marks:
        return {
            "student_id": student.get("student_id"),
            "roll_no": student.get("roll_no"),
            "name": student.get("name"),
            "section": student.get("section"),
            "total_marks_obtained": 0.0,
            "total_max_marks": 0.0,
            "average_marks": 0.0,
            "percentage": None,
            "grade": "N/A",
            "status": "No marks available",
            "subjects_taken": 0,
            "total_subjects": total_subjects_count,
            "missing_subjects_count": total_subjects_count,
            "failed_subjects_count": 0,
        }

    # Match relevant marks with known subjects
    subjects_by_id = {s["subject_id"]: s for s in all_subjects}
    
    total_obtained = 0.0
    total_max = 0.0
    failed_count = 0
    taken_sub_ids = set()

    for m in relevant_marks:
        sub_id = m.get("subject_id")
        sub_info = subjects_by_id.get(sub_id)
        if not sub_info:
            continue
            
        taken_sub_ids.add(sub_id)
        obtained = float(m.get("marks_obtained", 0.0))
        max_m = float(sub_info.get("max_marks", 100.0))
        pass_m = float(sub_info.get("pass_marks", 40.0))

        total_obtained += obtained
        total_max += max_m

        if obtained < pass_m:
            failed_count += 1

    subjects_taken_count = len(taken_sub_ids)
    missing_count = max(0, total_subjects_count - subjects_taken_count)

    # Safe division: never divide by zero
    if total_max > 0:
        percentage = round((total_obtained / total_max) * 100.0, 2)
        avg_marks = round(total_obtained / max(1, subjects_taken_count), 2)
    else:
        percentage = 0.0
        avg_marks = 0.0

    grade = calculate_grade(percentage)

    # Status Determination:
    # 1. If student hasn't completed all required subjects -> Incomplete
    # 2. If student failed any subject -> Fail
    # 3. Passed all subjects -> Pass
    if missing_count > 0:
        status = "Incomplete"
    elif failed_count > 0:
        status = "Fail"
    else:
        status = "Pass"

    return {
        "student_id": student.get("student_id"),
        "roll_no": student.get("roll_no"),
        "name": student.get("name"),
        "section": student.get("section"),
        "total_marks_obtained": round(total_obtained, 2),
        "total_max_marks": round(total_max, 2),
        "average_marks": avg_marks,
        "percentage": percentage,
        "grade": grade,
        "status": status,
        "subjects_taken": subjects_taken_count,
        "total_subjects": total_subjects_count,
        "missing_subjects_count": missing_count,
        "failed_subjects_count": failed_count,
    }


def generate_all_students_summary(
    students: List[Dict[str, Any]],
    all_marks: List[Dict[str, Any]],
    all_subjects: List[Dict[str, Any]],
    assessment: Optional[str] = None
) -> pd.DataFrame:
    """
    Generate comprehensive performance DataFrame for all students.
    Adds consistent competition ranking (ties receive equal ranks).
    Tie-breaking sort order: Percentage DESC, Total Marks DESC, Roll No ASC.
    """
    if not students:
        return pd.DataFrame(columns=[
            "Rank", "Roll No", "Name", "Section", "Total Obtained",
            "Total Max", "Average", "Percentage", "Grade", "Status",
            "Missing Subjects", "Failed Subjects", "student_id"
        ])

    # Group marks by student_id
    marks_by_student: Dict[int, List[Dict[str, Any]]] = {}
    for m in all_marks:
        sid = m.get("student_id")
        marks_by_student.setdefault(sid, []).append(m)

    summaries = []
    for s in students:
        sid = s.get("student_id")
        s_marks = marks_by_student.get(sid, [])
        summary = compute_student_summary(s, s_marks, all_subjects, assessment=assessment)
        summaries.append(summary)

    df = pd.DataFrame(summaries)
    if df.empty:
        return df

    # Replace None with np.nan for sorting
    df["percentage_numeric"] = pd.to_numeric(df["percentage"], errors="coerce")

    # Documented Tie-Breaking Display Order:
    # 1. Percentage (Highest to Lowest)
    # 2. Total Marks Obtained (Highest to Lowest)
    # 3. Roll Number (Alphabetical/Ascending)
    df = df.sort_values(
        by=["percentage_numeric", "total_marks_obtained", "roll_no"],
        ascending=[False, False, True]
    ).reset_index(drop=True)

    # Standard Competition Ranking ('min'):
    # Ties get equal rank (e.g. 1, 1, 3). Incomplete/No marks students get rank NaN or bottom rank
    df["Rank"] = df["percentage_numeric"].rank(method="min", ascending=False)
    # Format Rank cleanly
    df["Rank"] = df["Rank"].apply(lambda r: int(r) if pd.notna(r) else "-")

    # Format user-friendly columns
    display_df = df.rename(columns={
        "roll_no": "Roll No",
        "name": "Name",
        "section": "Section",
        "total_marks_obtained": "Total Obtained",
        "total_max_marks": "Total Max",
        "average_marks": "Average",
        "percentage": "Percentage",
        "grade": "Grade",
        "status": "Status",
        "missing_subjects_count": "Missing Subjects",
        "failed_subjects_count": "Failed Subjects"
    })

    columns_order = [
        "Rank", "Roll No", "Name", "Section", "Total Obtained",
        "Total Max", "Average", "Percentage", "Grade", "Status",
        "Missing Subjects", "Failed Subjects", "student_id"
    ]
    return display_df[[c for c in columns_order if c in display_df.columns]]


def get_top_performing_students(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    Return top-performing students ranked by percentage.
    Excludes students with incomplete status or no marks.
    Preserves equal ranks for ties.
    """
    if df.empty or "Percentage" not in df.columns:
        return pd.DataFrame()

    # Valid candidates: percentage must be numeric and status not 'No marks available'
    valid = df[df["Percentage"].notna() & (df["Status"] != "No marks available")].copy()
    if valid.empty:
        return pd.DataFrame()

    return valid.head(n)


def get_students_needing_support(df: pd.DataFrame, threshold: float = DEFAULT_SUPPORT_THRESHOLD) -> pd.DataFrame:
    """
    Return students who need academic support:
    - Percentage < configurable threshold (default: 50%) OR
    - Failed one or more subjects.
    Excludes students with no marks at all.
    """
    if df.empty or "Percentage" not in df.columns:
        return pd.DataFrame()

    # Filter students who have taken tests
    evaluated = df[df["Percentage"].notna() & (df["Status"] != "No marks available")].copy()
    if evaluated.empty:
        return pd.DataFrame()

    condition = (evaluated["Percentage"] < threshold) | (evaluated["Failed Subjects"] > 0)
    return evaluated[condition].copy()


def get_students_with_missing_marks(
    students: List[Dict[str, Any]],
    subjects: List[Dict[str, Any]],
    all_marks: List[Dict[str, Any]],
    assessment: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Find students who have not completed all required subjects for the assessment.
    Returns list of details specifying which subjects are missing.
    """
    if not students or not subjects:
        return []

    # Map marks by (student_id, assessment) -> set of subject_ids
    taken_map: Dict[int, set] = {}
    for m in all_marks:
        if assessment and assessment != "All / Primary" and m.get("assessment") != assessment:
            continue
        sid = m.get("student_id")
        sub_id = m.get("subject_id")
        taken_map.setdefault(sid, set()).add(sub_id)

    all_subject_ids = {s["subject_id"] for s in subjects}
    subject_names = {s["subject_id"]: s["subject_name"] for s in subjects}

    missing_list = []
    for s in students:
        sid = s["student_id"]
        taken_subs = taken_map.get(sid, set())
        missing_ids = all_subject_ids - taken_subs
        if missing_ids:
            missing_names = [subject_names[mid] for mid in missing_ids]
            missing_list.append({
                "student_id": sid,
                "roll_no": s["roll_no"],
                "name": s["name"],
                "section": s["section"],
                "missing_count": len(missing_ids),
                "missing_subjects": ", ".join(missing_names)
            })

    return missing_list


def get_subject_wise_summary(
    all_marks: List[Dict[str, Any]],
    all_subjects: List[Dict[str, Any]],
    assessment: Optional[str] = None
) -> pd.DataFrame:
    """
    Compute subject-level performance metrics:
    - Subject Name
    - Max Marks & Pass Marks
    - Total Students Evaluated
    - Average Marks Obtained
    - Pass Count & Fail Count
    - Pass Percentage (pass_count / total_evaluated * 100)
    - Highest & Lowest Marks
    """
    if not all_subjects:
        return pd.DataFrame()

    # Filter marks if assessment specified
    relevant_marks = all_marks
    if assessment and assessment != "All / Primary":
        relevant_marks = [m for m in all_marks if m.get("assessment") == assessment]

    marks_by_subject: Dict[int, List[float]] = {}
    for m in relevant_marks:
        sub_id = m.get("subject_id")
        marks_by_subject.setdefault(sub_id, []).append(float(m.get("marks_obtained", 0.0)))

    results = []
    for sub in all_subjects:
        sub_id = sub["subject_id"]
        sub_name = sub["subject_name"]
        max_m = float(sub["max_marks"])
        pass_m = float(sub["pass_marks"])

        scores = marks_by_subject.get(sub_id, [])
        total_eval = len(scores)

        if total_eval > 0:
            avg_score = round(float(np.mean(scores)), 2)
            passed = sum(1 for s in scores if s >= pass_m)
            failed = total_eval - passed
            pass_pct = round((passed / total_eval) * 100.0, 2)
            highest = round(float(np.max(scores)), 2)
            lowest = round(float(np.min(scores)), 2)
        else:
            avg_score = 0.0
            passed = 0
            failed = 0
            pass_pct = 0.0
            highest = 0.0
            lowest = 0.0

        results.append({
            "subject_id": sub_id,
            "Subject": sub_name,
            "Max Marks": max_m,
            "Pass Marks": pass_m,
            "Evaluated": total_eval,
            "Average Marks": avg_score,
            "Passed": passed,
            "Failed": failed,
            "Pass %": pass_pct,
            "Highest": highest,
            "Lowest": lowest
        })

    return pd.DataFrame(results)


def get_section_wise_summary(summary_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute section-wise performance comparison.
    """
    if summary_df.empty or "Section" not in summary_df.columns:
        return pd.DataFrame()

    sections = summary_df["Section"].unique()
    results = []

    for sec in sorted(sections):
        sec_df = summary_df[summary_df["Section"] == sec]
        total_s = len(sec_df)
        passed = sum(sec_df["Status"] == "Pass")
        failed = sum(sec_df["Status"] == "Fail")
        incomplete = sum(sec_df["Status"] == "Incomplete")
        no_marks = sum(sec_df["Status"] == "No marks available")

        # Average percentage across students who have marks
        valid_pcts = pd.to_numeric(sec_df["Percentage"], errors="coerce").dropna()
        avg_pct = round(float(valid_pcts.mean()), 2) if not valid_pcts.empty else 0.0

        # Section pass rate based on total students in section
        pass_rate = round((passed / total_s) * 100.0, 2) if total_s > 0 else 0.0

        results.append({
            "Section": sec,
            "Total Students": total_s,
            "Average %": avg_pct,
            "Passed": passed,
            "Failed": failed,
            "Incomplete": incomplete,
            "No Marks": no_marks,
            "Pass Rate %": pass_rate
        })

    return pd.DataFrame(results)


def get_class_summary(summary_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate class-level pass, fail, and completion metrics with documented denominators.
    - Pass % (Class) = (Passed / Total Students) * 100
    - Fail % (Class) = (Failed / Total Students) * 100
    - Incomplete % (Class) = (Incomplete / Total Students) * 100
    - Evaluated Pass % = (Passed / Evaluated Students) * 100
    """
    if summary_df.empty:
        return {
            "total_students": 0,
            "passed": 0,
            "failed": 0,
            "incomplete": 0,
            "no_marks": 0,
            "pass_percentage": 0.0,
            "fail_percentage": 0.0,
            "incomplete_percentage": 0.0,
            "evaluated_pass_percentage": 0.0,
            "class_average_percentage": 0.0
        }

    total = len(summary_df)
    passed = int((summary_df["Status"] == "Pass").sum())
    failed = int((summary_df["Status"] == "Fail").sum())
    incomplete = int((summary_df["Status"] == "Incomplete").sum())
    no_marks = int((summary_df["Status"] == "No marks available").sum())

    evaluated = total - no_marks

    valid_pcts = pd.to_numeric(summary_df["Percentage"], errors="coerce").dropna()
    class_avg = round(float(valid_pcts.mean()), 2) if not valid_pcts.empty else 0.0

    return {
        "total_students": total,
        "passed": passed,
        "failed": failed,
        "incomplete": incomplete,
        "no_marks": no_marks,
        "pass_percentage": round((passed / total) * 100.0, 2) if total > 0 else 0.0,
        "fail_percentage": round((failed / total) * 100.0, 2) if total > 0 else 0.0,
        "incomplete_percentage": round((incomplete / total) * 100.0, 2) if total > 0 else 0.0,
        "evaluated_pass_percentage": round((passed / evaluated) * 100.0, 2) if evaluated > 0 else 0.0,
        "class_average_percentage": class_avg
    }

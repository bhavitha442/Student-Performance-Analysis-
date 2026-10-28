"""
test_analysis.py
====================================================================
Unit Tests for Academic Calculations & Analysis Engine
Tests grading, pass/fail rules, rankings, ties, missing marks,
and summary reports with zero external dependencies.
====================================================================
"""

import pytest
import sys
import os
import pandas as pd
import io

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analysis import (
    calculate_grade,
    compute_student_summary,
    generate_all_students_summary,
    get_top_performing_students,
    get_students_needing_support,
    get_students_with_missing_marks,
    get_subject_wise_summary,
    get_section_wise_summary,
    get_class_summary,
)
from database import test_db_connection as check_db_connection, get_db_connection


class TestGradingRules:
    """Verify grade boundaries conform strictly to academic specification."""

    def test_grade_a(self):
        assert calculate_grade(100.0) == "A"
        assert calculate_grade(95.5) == "A"
        assert calculate_grade(90.0) == "A"

    def test_grade_b(self):
        assert calculate_grade(89.9) == "B"
        assert calculate_grade(85.0) == "B"
        assert calculate_grade(80.0) == "B"

    def test_grade_c(self):
        assert calculate_grade(79.9) == "C"
        assert calculate_grade(70.0) == "C"

    def test_grade_d(self):
        assert calculate_grade(69.9) == "D"
        assert calculate_grade(60.0) == "D"

    def test_grade_e(self):
        assert calculate_grade(59.9) == "E"
        assert calculate_grade(50.0) == "E"

    def test_grade_f(self):
        assert calculate_grade(49.9) == "F"
        assert calculate_grade(30.0) == "F"
        assert calculate_grade(0.0) == "F"

    def test_grade_none_or_nan(self):
        assert calculate_grade(None) == "N/A"
        assert calculate_grade(float("nan")) == "N/A"


class TestStudentSummaryCalculations:
    """Tests for single student calculations, pass/fail status, and missing marks."""

    @pytest.fixture
    def sample_subjects(self):
        return [
            {"subject_id": 1, "subject_name": "Mathematics", "max_marks": 100.0, "pass_marks": 40.0},
            {"subject_id": 2, "subject_name": "Python Programming", "max_marks": 100.0, "pass_marks": 40.0},
            {"subject_id": 3, "subject_name": "Digital Logic", "max_marks": 100.0, "pass_marks": 40.0},
        ]

    def test_topper_student_pass(self, sample_subjects):
        student = {"student_id": 101, "roll_no": "101", "name": "Arun Kumar", "section": "A"}
        marks = [
            {"subject_id": 1, "assessment": "Final Exam", "marks_obtained": 95.0},
            {"subject_id": 2, "assessment": "Final Exam", "marks_obtained": 92.0},
            {"subject_id": 3, "assessment": "Final Exam", "marks_obtained": 90.0},
        ]
        res = compute_student_summary(student, marks, sample_subjects, assessment="Final Exam")

        assert res["total_marks_obtained"] == 277.0
        assert res["total_max_marks"] == 300.0
        assert res["percentage"] == 92.33
        assert res["grade"] == "A"
        assert res["status"] == "Pass"
        assert res["missing_subjects_count"] == 0
        assert res["failed_subjects_count"] == 0

    def test_student_failing_one_subject(self, sample_subjects):
        # Even with high marks in others, failing one subject makes overall status Fail
        student = {"student_id": 103, "roll_no": "103", "name": "Rahul Verma", "section": "B"}
        marks = [
            {"subject_id": 1, "assessment": "Final Exam", "marks_obtained": 35.0},  # Failed (< 40)
            {"subject_id": 2, "assessment": "Final Exam", "marks_obtained": 75.0},
            {"subject_id": 3, "assessment": "Final Exam", "marks_obtained": 65.0},
        ]
        res = compute_student_summary(student, marks, sample_subjects, assessment="Final Exam")

        assert res["total_marks_obtained"] == 175.0
        assert res["percentage"] == 58.33
        assert res["grade"] == "E"
        assert res["status"] == "Fail"
        assert res["failed_subjects_count"] == 1

    def test_student_with_missing_marks_is_incomplete(self, sample_subjects):
        # A student who has not taken all 3 subjects must be 'Incomplete', never 'Pass'
        student = {"student_id": 105, "roll_no": "105", "name": "Kiran Das", "section": "A"}
        marks = [
            {"subject_id": 1, "assessment": "Final Exam", "marks_obtained": 80.0},
        ]
        res = compute_student_summary(student, marks, sample_subjects, assessment="Final Exam")

        assert res["status"] == "Incomplete"
        assert res["missing_subjects_count"] == 2
        assert res["subjects_taken"] == 1

    def test_student_with_zero_marks(self, sample_subjects):
        # No division by zero when student has no marks records
        student = {"student_id": 999, "roll_no": "999", "name": "New Student", "section": "A"}
        res = compute_student_summary(student, [], sample_subjects, assessment="Final Exam")

        assert res["status"] == "No marks available"
        assert res["percentage"] is None
        assert res["grade"] == "N/A"
        assert res["total_marks_obtained"] == 0.0


class TestRankingAndTies:
    """Verify ranking logic and handling of ties."""

    def test_ranking_ties_equal_ranks(self):
        subjects = [
            {"subject_id": 1, "subject_name": "Math", "max_marks": 100.0, "pass_marks": 40.0},
            {"subject_id": 2, "subject_name": "CS", "max_marks": 100.0, "pass_marks": 40.0},
        ]
        students = [
            {"student_id": 1, "roll_no": "101", "name": "Arun", "section": "A"},
            {"student_id": 2, "roll_no": "102", "name": "Priya", "section": "A"},
            {"student_id": 3, "roll_no": "103", "name": "Third", "section": "B"},
        ]
        # Both Arun and Priya have identical 90%
        marks = [
            {"student_id": 1, "subject_id": 1, "assessment": "Exam", "marks_obtained": 90.0},
            {"student_id": 1, "subject_id": 2, "assessment": "Exam", "marks_obtained": 90.0},
            {"student_id": 2, "subject_id": 1, "assessment": "Exam", "marks_obtained": 90.0},
            {"student_id": 2, "subject_id": 2, "assessment": "Exam", "marks_obtained": 90.0},
            {"student_id": 3, "subject_id": 1, "assessment": "Exam", "marks_obtained": 70.0},
            {"student_id": 3, "subject_id": 2, "assessment": "Exam", "marks_obtained": 70.0},
        ]

        df = generate_all_students_summary(students, marks, subjects, assessment="Exam")

        # Rank column should assign Rank 1 to both toppers, and Rank 3 to the next student
        arun_rank = df[df["Roll No"] == "101"]["Rank"].values[0]
        priya_rank = df[df["Roll No"] == "102"]["Rank"].values[0]
        third_rank = df[df["Roll No"] == "103"]["Rank"].values[0]

        assert arun_rank == 1
        assert priya_rank == 1
        assert third_rank == 3


class TestAcademicSupportAndReports:
    """Verify filtering for academic support and toppers."""

    def test_students_needing_support(self):
        data = {
            "Rank": [1, 2, 3],
            "Roll No": ["101", "103", "104"],
            "Name": ["Arun", "Rahul", "Sneha"],
            "Section": ["A", "B", "B"],
            "Total Obtained": [277, 175, 131],
            "Total Max": [300, 300, 300],
            "Average": [92.33, 58.33, 43.67],
            "Percentage": [92.33, 58.33, 43.67],
            "Grade": ["A", "E", "F"],
            "Status": ["Pass", "Fail", "Fail"],
            "Missing Subjects": [0, 0, 0],
            "Failed Subjects": [0, 1, 1],
        }
        df = pd.DataFrame(data)

        support_df = get_students_needing_support(df, threshold=50.0)
        # Rahul (failed subjects = 1) and Sneha (< 50% and failed) both need support
        assert len(support_df) == 2
        assert "Rahul" in support_df["Name"].values
        assert "Sneha" in support_df["Name"].values
        assert "Arun" not in support_df["Name"].values

    def test_class_summary_metrics(self):
        data = {
            "Roll No": ["101", "102", "103", "104", "105"],
            "Percentage": [92.33, 92.33, 58.33, 43.67, 80.0],
            "Status": ["Pass", "Pass", "Fail", "Fail", "Incomplete"],
        }
        df = pd.DataFrame(data)
        metrics = get_class_summary(df)

        assert metrics["total_students"] == 5
        assert metrics["passed"] == 2
        assert metrics["failed"] == 2
        assert metrics["incomplete"] == 1
        assert metrics["pass_percentage"] == 40.0  # 2 / 5 * 100
        assert metrics["fail_percentage"] == 40.0  # 2 / 5 * 100
        assert metrics["incomplete_percentage"] == 20.0  # 1 / 5 * 100


class TestSubjectSummaryAndMissingMarks:
    """Verify subject averages and missing marks detection."""

    def test_subject_wise_summary(self):
        subjects = [
            {"subject_id": 1, "subject_name": "Math", "max_marks": 100.0, "pass_marks": 40.0},
        ]
        marks = [
            {"subject_id": 1, "assessment": "Final", "marks_obtained": 90.0},
            {"subject_id": 1, "assessment": "Final", "marks_obtained": 30.0},
        ]
        sub_df = get_subject_wise_summary(marks, subjects, assessment="Final")
        assert len(sub_df) == 1
        row = sub_df.iloc[0]
        assert row["Evaluated"] == 2
        assert row["Average Marks"] == 60.0
        assert row["Passed"] == 1
        assert row["Failed"] == 1
        assert row["Pass %"] == 50.0
        assert row["Highest"] == 90.0
        assert row["Lowest"] == 30.0

    def test_missing_marks_detection(self):
        students = [
            {"student_id": 1, "roll_no": "101", "name": "Arun", "section": "A"},
            {"student_id": 2, "roll_no": "105", "name": "Kiran", "section": "A"},
        ]
        subjects = [
            {"subject_id": 1, "subject_name": "Math"},
            {"subject_id": 2, "subject_name": "Python"},
        ]
        marks = [
            {"student_id": 1, "subject_id": 1, "assessment": "Final", "marks_obtained": 90.0},
            {"student_id": 1, "subject_id": 2, "assessment": "Final", "marks_obtained": 90.0},
            {"student_id": 2, "subject_id": 1, "assessment": "Final", "marks_obtained": 80.0},
            # Kiran is missing subject 2
        ]
        missing = get_students_with_missing_marks(students, subjects, marks, assessment="Final")
        assert len(missing) == 1
        assert missing[0]["roll_no"] == "105"
        assert missing[0]["missing_count"] == 1
        assert "Python" in missing[0]["missing_subjects"]


class TestCSVExportFormatting:
    """Verify that DataFrames generate valid, readable CSV streams with proper headers."""

    def test_csv_generation(self):
        data = {
            "Rank": [1],
            "Roll No": ["101"],
            "Name": ["Arun Kumar"],
            "Section": ["A"],
            "Percentage": [92.33],
            "Grade": ["A"],
            "Status": ["Pass"],
        }
        df = pd.DataFrame(data)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_text = csv_buffer.getvalue()

        assert "Rank,Roll No,Name,Section,Percentage,Grade,Status" in csv_text
        assert "1,101,Arun Kumar,A,92.33,A,Pass" in csv_text


class TestDatabaseConnectionFailureGracefulness:
    """Verify database connection failure handling when service is down."""

    def test_db_connection_diagnostic_message(self):
        # Since MySQL service is currently down or credentials not set, check_db_connection returns (False, msg)
        # without crashing
        is_connected, msg = check_db_connection()
        assert isinstance(is_connected, bool)
        assert isinstance(msg, str)
        if not is_connected:
            assert len(msg) > 0
            # Diagnostics should mention host or connection failure
            assert any(word in msg.lower() for word in ["connect", "mysql", "access", "database", "service"])

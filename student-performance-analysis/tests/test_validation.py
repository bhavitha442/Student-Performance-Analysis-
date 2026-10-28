"""
test_validation.py
====================================================================
Unit Tests for Input Validation Logic
Tests all validation functions independently without requiring MySQL.
====================================================================
"""

import pytest
import sys
import os

# Add parent directory to sys.path so we can import project modules cleanly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from student_operations import validate_student_data
from subject_operations import validate_subject_data
from marks_operations import validate_marks_data


class TestStudentValidation:
    """Tests for student input validation."""

    def test_valid_student(self):
        is_valid, msg = validate_student_data("101", "Arun Kumar", "A")
        assert is_valid is True
        assert msg == ""

    def test_empty_roll_number(self):
        is_valid, msg = validate_student_data("", "Arun Kumar", "A")
        assert is_valid is False
        assert "Roll number is required" in msg

        is_valid, msg = validate_student_data("   ", "Arun Kumar", "A")
        assert is_valid is False
        assert "Roll number is required" in msg

    def test_empty_name(self):
        is_valid, msg = validate_student_data("101", "", "A")
        assert is_valid is False
        assert "Student name is required" in msg

        is_valid, msg = validate_student_data("101", "   ", "A")
        assert is_valid is False
        assert "Student name is required" in msg

    def test_empty_section(self):
        is_valid, msg = validate_student_data("101", "Arun Kumar", "")
        assert is_valid is False
        assert "Section is required" in msg

    def test_exceeding_lengths(self):
        is_valid, msg = validate_student_data("R" * 51, "Valid Name", "A")
        assert is_valid is False
        assert "50 characters" in msg

        is_valid, msg = validate_student_data("101", "N" * 101, "A")
        assert is_valid is False
        assert "100 characters" in msg

        is_valid, msg = validate_student_data("101", "Valid Name", "S" * 21)
        assert is_valid is False
        assert "20 characters" in msg


class TestSubjectValidation:
    """Tests for subject input validation."""

    def test_valid_subject(self):
        is_valid, msg, max_m, pass_m = validate_subject_data("Mathematics", 100, 40)
        assert is_valid is True
        assert msg == ""
        assert max_m == 100.0
        assert pass_m == 40.0

    def test_empty_subject_name(self):
        is_valid, msg, _, _ = validate_subject_data("", 100, 40)
        assert is_valid is False
        assert "Subject name cannot be empty" in msg

    def test_zero_or_negative_max_marks(self):
        is_valid, msg, _, _ = validate_subject_data("Physics", 0, 0)
        assert is_valid is False
        assert "greater than zero" in msg

        is_valid, msg, _, _ = validate_subject_data("Physics", -50, 20)
        assert is_valid is False
        assert "greater than zero" in msg

    def test_zero_or_negative_pass_marks(self):
        is_valid, msg, _, _ = validate_subject_data("Chemistry", 100, 0)
        assert is_valid is False
        assert "Pass marks must be greater than zero" in msg

        is_valid, msg, _, _ = validate_subject_data("Chemistry", 100, -10)
        assert is_valid is False
        assert "Pass marks must be greater than zero" in msg

    def test_pass_marks_exceeding_max_marks(self):
        is_valid, msg, _, _ = validate_subject_data("Biology", 100, 105)
        assert is_valid is False
        assert "cannot exceed maximum marks" in msg

    def test_non_numeric_marks(self):
        is_valid, msg, _, _ = validate_subject_data("English", "abc", 40)
        assert is_valid is False
        assert "valid number" in msg

        is_valid, msg, _, _ = validate_subject_data("English", 100, "xyz")
        assert is_valid is False
        assert "valid number" in msg


class TestMarksValidation:
    """Tests for marks input validation."""

    def test_valid_marks(self):
        is_valid, msg, val = validate_marks_data(1, 2, "Final Exam", 85.5, max_marks=100.0)
        assert is_valid is True
        assert msg == ""
        assert val == 85.5

    def test_negative_marks_rejected(self):
        is_valid, msg, _ = validate_marks_data(1, 2, "Final Exam", -5.0, max_marks=100.0)
        assert is_valid is False
        assert "cannot be negative" in msg

    def test_marks_exceeding_max_marks_rejected(self):
        is_valid, msg, _ = validate_marks_data(1, 2, "Final Exam", 105.0, max_marks=100.0)
        assert is_valid is False
        assert "cannot exceed the subject maximum marks" in msg

    def test_empty_assessment_name(self):
        is_valid, msg, _ = validate_marks_data(1, 2, "", 50.0, max_marks=100.0)
        assert is_valid is False
        assert "Assessment name is required" in msg

    def test_empty_student_or_subject(self):
        is_valid, msg, _ = validate_marks_data(None, 2, "Midterm", 50.0, max_marks=100.0)
        assert is_valid is False
        assert "Student selection is required" in msg

        is_valid, msg, _ = validate_marks_data(1, None, "Midterm", 50.0, max_marks=100.0)
        assert is_valid is False
        assert "Subject selection is required" in msg

    def test_non_numeric_marks(self):
        is_valid, msg, _ = validate_marks_data(1, 2, "Midterm", "invalid_mark", max_marks=100.0)
        assert is_valid is False
        assert "valid number" in msg

-- ====================================================================
-- Student Performance Analysis System - Database Schema
-- Database: student_performance_db
-- Compatible with MySQL 8.0+
-- ====================================================================

-- Create the database if it doesn't already exist
CREATE DATABASE IF NOT EXISTS student_performance_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE student_performance_db;

-- --------------------------------------------------------------------
-- 1. Students Table
-- --------------------------------------------------------------------
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

-- --------------------------------------------------------------------
-- 2. Subjects Table
-- --------------------------------------------------------------------
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

-- --------------------------------------------------------------------
-- 3. Marks Table
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marks (
    mark_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    assessment VARCHAR(50) NOT NULL,
    marks_obtained DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Prevent negative marks
    CONSTRAINT chk_marks_obtained_non_negative CHECK (marks_obtained >= 0),
    -- Ensure assessment string is not blank
    CONSTRAINT chk_assessment_not_empty CHECK (LENGTH(TRIM(assessment)) > 0),
    -- Foreign keys with safe integrity rules
    CONSTRAINT fk_marks_student FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_marks_subject FOREIGN KEY (subject_id)
        REFERENCES subjects(subject_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    -- Prevent duplicate records for the same student, subject, and assessment
    CONSTRAINT uq_student_subject_assessment UNIQUE (student_id, subject_id, assessment)
) ENGINE=InnoDB;

-- Useful indexes for query performance
CREATE INDEX idx_marks_student ON marks(student_id);
CREATE INDEX idx_marks_subject ON marks(subject_id);
CREATE INDEX idx_marks_assessment ON marks(assessment);

-- --------------------------------------------------------------------
-- 4. Sample Fictional Data (Optional)
-- --------------------------------------------------------------------
-- Insert sample subjects
INSERT IGNORE INTO subjects (subject_name, max_marks, pass_marks) VALUES
('Mathematics', 100.00, 40.00),
('Python Programming', 100.00, 40.00),
('Digital Logic Design', 100.00, 40.00);

-- Insert sample fictional students
INSERT IGNORE INTO students (roll_no, name, section) VALUES
('101', 'Arun Kumar', 'A'),
('102', 'Priya Sharma', 'A'),
('103', 'Rahul Verma', 'B'),
('104', 'Sneha Reddy', 'B'),
('105', 'Kiran Das', 'A');

-- Insert sample marks for 'Final Exam'
-- Arun Kumar: High achiever (Topper 1 - 277/300 = 92.33%)
-- Priya Sharma: Equal high score tie (Topper 2 - 277/300 = 92.33%)
-- Rahul Verma: Failed in one subject (Mathematics: 35 < 40 -> Overall Fail)
-- Sneha Reddy: Needs academic support (Math 42, Python 45, DLD 44 -> Avg 43.67% < 50%)
-- Kiran Das: Missing marks (only took Mathematics: 80 -> Incomplete status)
INSERT IGNORE INTO marks (student_id, subject_id, assessment, marks_obtained)
SELECT s.student_id, sub.subject_id, 'Final Exam', vals.marks
FROM (
    SELECT '101' AS roll_no, 'Mathematics' AS subject_name, 95.00 AS marks UNION ALL
    SELECT '101', 'Python Programming', 92.00 UNION ALL
    SELECT '101', 'Digital Logic Design', 90.00 UNION ALL
    SELECT '102', 'Mathematics', 90.00 UNION ALL
    SELECT '102', 'Python Programming', 95.00 UNION ALL
    SELECT '102', 'Digital Logic Design', 92.00 UNION ALL
    SELECT '103', 'Mathematics', 35.00 UNION ALL
    SELECT '103', 'Python Programming', 75.00 UNION ALL
    SELECT '103', 'Digital Logic Design', 65.00 UNION ALL
    SELECT '104', 'Mathematics', 42.00 UNION ALL
    SELECT '104', 'Python Programming', 45.00 UNION ALL
    SELECT '104', 'Digital Logic Design', 44.00 UNION ALL
    SELECT '105', 'Mathematics', 80.00
) AS vals
JOIN students s ON s.roll_no = vals.roll_no
JOIN subjects sub ON sub.subject_name = vals.subject_name;

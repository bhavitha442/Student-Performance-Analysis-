# 🎓 Student Performance Analysis System

A modular, beginner-friendly academic analytics web application built with **Python 3, Streamlit, Pandas, NumPy, Matplotlib, and MySQL**.

Designed for first-year B.Tech students and educators to track student grades, analyze subject pass rates, identify students who need academic support, and visualize academic trends with exportable reports.

---

## 📁 Project Architecture & File Structure

```text
Student Performance Analysis/
├── app.py                     # Convenience launcher for Streamlit application
├── requirements.txt           # Project dependencies
├── .env.example               # Template for MySQL credentials
├── .gitignore                 # Files excluded from Git tracking (secrets, cache, venv)
├── README.md                  # Comprehensive Windows setup and user guide
└── student-performance-analysis/
    ├── app.py                 # Streamlit multi-page web application controller
    ├── database.py            # Secure MySQL connection, configuration, and table initializers
    ├── student_operations.py  # Student CRUD operations, validations, and search
    ├── subject_operations.py  # Subject CRUD operations, maximum & pass marks validation
    ├── marks_operations.py    # Marks entry, duplicate prevention, and consistency checks
    ├── analysis.py            # Academic grading logic, competition ranking, pass/fail rules
    ├── visualizations.py      # Matplotlib chart generators (averages, distributions, sections)
    ├── load_sample_data.py    # CLI script to populate database with fictional test data
    ├── database.sql           # Complete MySQL DDL schema and sample records
    ├── requirements.txt       # Project dependencies
    ├── .env.example           # Template for MySQL credentials
    ├── .gitignore             # Git ignore patterns
    ├── README.md              # Documentation
    └── tests/
        ├── test_validation.py # Unit tests for input validation functions
        └── test_analysis.py   # Unit tests for grading, ranking, pass/fail, and CSV generation
```

---

## 🚀 Quick Start for Windows

### 1. Run Automated Unit Tests (35 Tests)
```powershell
& "C:\Users\M Bhavitha\AppData\Local\Programs\Python\Python314\python.exe" -m pytest -q
```
*(All 35 tests pass with 0 warnings without requiring an active database).*

### 2. Start MySQL Server
Ensure the MySQL Windows Service is started:
- Press `Win + R` -> type `services.msc` -> start **MySQL80**.
- Or run in Admin PowerShell: `net start MySQL80`

### 3. Set Up `.env` File
```powershell
Copy-Item .env.example .env
```
Open `.env` and enter your MySQL root password:
```env
DB_PASSWORD=your_actual_password_here
```

### 4. Run the Streamlit Application
```powershell
& "C:\Users\M Bhavitha\AppData\Local\Programs\Python\Python314\python.exe" -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

Please refer to [`student-performance-analysis/README.md`](file:///c:/Users/M%20Bhavitha/Downloads/Student%20Performance%20Analysis/student-performance-analysis/README.md) for full documentation, grading scales, tie-breaking rules, and troubleshooting tips.

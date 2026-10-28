# 🎓 Student Performance Analysis System

A modular, beginner-friendly academic analytics web application built with **Python 3, Streamlit, Pandas, NumPy, Matplotlib, and MySQL**.

Designed for first-year B.Tech students and educators to track student grades, analyze subject pass rates, identify students who need academic support, and visualize academic trends with exportable reports.

---

## 📁 Project Architecture & File Structure

```text
student-performance-analysis/
├── app.py                     # Streamlit multi-page web application controller
├── database.py                # Secure MySQL connection, configuration, and table initializers
├── student_operations.py      # Student CRUD operations, validations, and search
├── subject_operations.py      # Subject CRUD operations, maximum & pass marks validation
├── marks_operations.py        # Marks entry, duplicate prevention, and consistency checks
├── analysis.py                # Academic grading logic, competition ranking, pass/fail rules
├── visualizations.py          # Matplotlib chart generators (averages, distributions, sections)
├── load_sample_data.py        # CLI script to populate database with fictional test data
├── database.sql               # Complete MySQL DDL schema and sample records
├── requirements.txt           # Project dependencies
├── .env.example               # Template for MySQL credentials
├── .gitignore                 # Files excluded from Git tracking (secrets, cache, venv)
├── README.md                  # Detailed beginner setup and execution guide
└── tests/
    ├── test_validation.py     # Unit tests for input validation functions
    └── test_analysis.py       # Unit tests for grading, ranking, pass/fail, and CSV generation
```

### Module Roles & Responsibilities

| File | Purpose |
| :--- | :--- |
| `app.py` | Runs the Streamlit dashboard with sidebar navigation, metric cards, interactive forms, and export triggers. |
| `database.py` | Connects securely to MySQL using `.env` environment variables, initializes schema, and provides diagnostic checks. |
| `student_operations.py` | Handles adding, searching, updating, and deleting students with duplicate roll number prevention. |
| `subject_operations.py` | Manages subjects with validation ensuring maximum marks > 0 and pass marks ≤ maximum marks. |
| `marks_operations.py` | Records assessment scores with validation against subject limits and duplicate submission prevention. |
| `analysis.py` | Core calculation engine implementing percentage, letter grades (A–F), competition ranking (with tie handling), and academic support flagging. |
| `visualizations.py` | Generates 5 distinct Matplotlib visualizations with empty-state placeholders. |
| `load_sample_data.py` | Optional CLI loader to populate fictional students, subjects, and test scores. |
| `tests/` | Automated test suite verifying validation rules and mathematical calculations. |

---

## 🚀 Beginner Setup Guide for Windows

Follow these steps one by one to configure and run the application on your Windows computer.

---

### Step 1: Open the Project in Visual Studio Code

1. Launch **Visual Studio Code**.
2. Click **File** > **Open Folder...** (or press `Ctrl + K`, `Ctrl + O`).
3. Navigate to and select this project directory:
   `C:\Users\M Bhavitha\Downloads\Student Performance Analysis`
4. Open the integrated terminal by pressing `` Ctrl + ` `` (Backtick) or clicking **Terminal** > **New Terminal**.

---

### Step 2: Verify or Fix Python on Windows

Python 3.14 is installed on your computer at:
`C:\Users\M Bhavitha\AppData\Local\Programs\Python\Python314\python.exe`

If typing `python` in PowerShell shows an error or opens the Windows Store, use the Python launcher `py` or specify the exact path.

Test your Python installation by running:
```powershell
& "C:\Users\M Bhavitha\AppData\Local\Programs\Python\Python314\python.exe" --version
```
*Expected output:* `Python 3.14.x`

> **Tip:** You can install the official **Python extension** in VS Code:
> 1. Press `Ctrl + Shift + X` to open the Extensions tab.
> 2. Search for `Python` (published by Microsoft).
> 3. Click **Install**.
> 4. Press `Ctrl + Shift + P`, type `Python: Select Interpreter`, and select `Python 3.14.x`.

---

### Step 3: Create & Activate a Virtual Environment

A virtual environment isolates your project packages so they don't interfere with other Python software on your system.

1. **Create the virtual environment:**
   ```powershell
   & "C:\Users\M Bhavitha\AppData\Local\Programs\Python\Python314\python.exe" -m venv .venv
   ```

2. **Allow PowerShell script execution (if prompted with execution policy errors):**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Activate the environment:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   *When active, you will see `(.venv)` at the beginning of your terminal prompt.*

---

### Step 4: Install Dependencies

With the virtual environment activated, install the required packages:

```powershell
python -m pip install -r requirements.txt
```

*What this command does:* Reads `requirements.txt` and installs Streamlit, Pandas, NumPy, Matplotlib, mysql-connector-python, python-dotenv, and pytest.

---

### Step 5: Start MySQL Server Service

Your computer has MySQL Server 8.0 installed at `C:\Program Files\MySQL\MySQL Server 8.0\`.
The MySQL Windows service must be running for the database to accept connections.

1. Press `Windows Key + R`, type `services.msc`, and press **Enter**.
2. Scroll down to find **MySQL80** (or **MySQL**).
3. If its status is not "Running", right-click it and click **Start**.
4. Alternatively, open **PowerShell as Administrator** and run:
   ```powershell
   net start MySQL80
   ```

---

### Step 6: Configure Environment Credentials (`.env`)

1. In the project folder, locate `.env.example`.
2. Copy it and create a new file named `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
3. Open `.env` in VS Code and fill in your MySQL root password:
   ```env
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_actual_password_here
   DB_NAME=student_performance_db
   ```
4. Save the file (`Ctrl + S`).

> 🔒 **Security Notice:** The `.env` file is listed in `.gitignore` so your password will never be committed to Git or shared publicly.

---

### Step 7: Initialize Database & Load Sample Data

You can initialize the database using either method:

#### Option A: Using the CLI Loader (Recommended)
Run the automated initialization and sample data loader:
```powershell
python student-performance-analysis/load_sample_data.py
```
*(Or if inside `student-performance-analysis`: `python load_sample_data.py`)*

#### Option B: Using the Web UI
1. Launch the web app (Step 8).
2. Click **🛠️ Init DB** in the sidebar.
3. Click **📥 Sample Data** in the sidebar.

#### Option C: Using MySQL Command Line or Workbench
```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p < student-performance-analysis/database.sql
```

---

### Step 8: Start the Streamlit Application

Run the application:
```powershell
python -m streamlit run app.py
```

*What happens:* Streamlit launches a local web server and automatically opens your default browser at:
`http://localhost:8501`

To stop the web server when you are done, return to the terminal and press `Ctrl + C`.

---

### Step 9: Run the Automated Unit Tests

Run the comprehensive pytest suite:
```powershell
python -m pytest -q
```
*Expected result:* `35 passed in ~1.8s`

To run with verbose per-test details:
```powershell
python -m pytest -v
```

---

## 📊 Academic Rules & Calculation Standards

### 1. Grading Scale
| Percentage Range | Grade | Meaning |
| :---: | :---: | :--- |
| **90% – 100%** | **A** | Outstanding / Distinction |
| **80% – <90%** | **B** | Very Good |
| **70% – <80%** | **C** | Good |
| **60% – <70%** | **D** | Average |
| **50% – <60%** | **E** | Pass Threshold |
| **Below 50%** | **F** | Fail / Academic Support Required |

### 2. Pass / Fail Rules
- **Subject Pass Rule:** A student passes a subject if and only if $\text{marks\_obtained} \ge \text{pass\_marks}$.
- **Overall Class Result:**
  - **PASS:** Student has appeared in **all required subjects** AND scored $\ge \text{pass\_marks}$ in **every** subject.
  - **FAIL:** Student scored below pass marks in one or more subjects.
  - **INCOMPLETE:** Student has not taken tests for all required curriculum subjects. Incomplete results are **never** declared as PASS.

### 3. Competition Ranking & Ties
- Students are ranked using standard **competition ranking (`rank(method='min')`)**.
- Ties with equal percentages receive equal ranks (e.g. Arun: Rank 1, Priya: Rank 1, Third Student: Rank 3).
- **Documented Tie-Breaking Display Order:**
  1. Percentage (Highest to Lowest)
  2. Total Marks Obtained (Highest to Lowest)
  3. Roll Number (Ascending)

---

## 🛠️ Common Troubleshooting Tips

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `The file cannot be accessed by the system` | Windows Store app alias intercepting `python.exe` | Run with full path `& "C:\Users\M Bhavitha\AppData\Local\Programs\Python\Python314\python.exe"`, or use Python in `.venv`. |
| `Cannot connect to MySQL server on localhost:3306` | MySQL Service is stopped | Open `services.msc`, locate `MySQL80`, and click **Start**. |
| `Access denied for user 'root'@'localhost'` | Wrong password in `.env` | Check your `.env` file and verify your `DB_PASSWORD`. |
| `Script execution is disabled on this system` | PowerShell ExecutionPolicy | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell. |
| Duplicate marks entry error in UI | Student already has marks for that subject and assessment | Edit the existing record in the **✏️ Edit Mark** tab instead of creating a duplicate. |

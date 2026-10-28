"""
load_sample_data.py
====================================================================
Sample Data CLI Loader
Populates student_performance_db with fictional students, subjects,
and assessment marks for testing and grading.
====================================================================
"""

import sys
from database import init_db, load_sample_data, test_db_connection


def main():
    print("=" * 60)
    print("Student Performance Analysis System - Sample Data Loader")
    print("=" * 60)

    print("\n1. Initializing database and tables...")
    init_ok, init_msg = init_db()
    if not init_ok:
        print(f"[ERROR] Schema init failed: {init_msg}")
        sys.exit(1)
    print(f"[OK] {init_msg}")

    print("\n2. Verifying database connection...")
    ok, msg = test_db_connection()
    if not ok:
        print(f"[ERROR] Database connection failed: {msg}")
        sys.exit(1)
    print(f"[OK] {msg}")

    print("\n3. Loading fictional sample records...")
    load_ok, load_msg = load_sample_data()
    if not load_ok:
        print(f"[ERROR] Loading sample data failed: {load_msg}")
        sys.exit(1)
    print(f"[SUCCESS] {load_msg}")
    print("\nYou can now start the Streamlit web application: streamlit run app.py")


if __name__ == "__main__":
    main()

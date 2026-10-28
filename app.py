"""
Root entry point for Student Performance Analysis System.
Delegates execution to student-performance-analysis/app.py.
"""
import os
import sys

# Ensure student-performance-analysis is on sys.path and is current working directory
current_dir = os.path.dirname(os.path.abspath(__file__))
pkg_dir = os.path.join(current_dir, "student-performance-analysis")

if os.path.exists(pkg_dir):
    sys.path.insert(0, pkg_dir)
    os.chdir(pkg_dir)

from app import main

if __name__ == "__main__":
    main()

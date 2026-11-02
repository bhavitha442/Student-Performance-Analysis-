@echo off
title Student Performance Analysis System
echo ===================================================
echo Starting Student Performance Analysis System...
echo ===================================================
cd /d "%~dp0"
"C:\Users\M Bhavitha\AppData\Local\Programs\Python\Python314\python.exe" -m streamlit run app.py
pause

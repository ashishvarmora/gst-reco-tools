@echo off
title GST Reconciliation Dashboard
echo.
echo ====================================
echo    GST Reconciliation Dashboard
echo ====================================
echo.
echo Starting the dashboard...
echo Dashboard will open in your browser at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the dashboard
echo.
streamlit run complete_dashboard.py
pause
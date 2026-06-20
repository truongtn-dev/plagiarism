@echo off
title IEEE Plagiarism Checker
cd /d "%~dp0"
echo Installing dependencies...
pip install -r requirements.txt -q
echo.
echo Starting Plagiarism Checker UI...
echo Open http://localhost:8501 in your browser
echo.
streamlit run app.py --server.headless true
pause

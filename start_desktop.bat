@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
pythonw run_app.py
exit

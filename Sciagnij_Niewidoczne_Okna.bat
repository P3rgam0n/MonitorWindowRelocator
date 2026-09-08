@echo off
python "%~dp0main.py" --gather
timeout /t 2 > nul

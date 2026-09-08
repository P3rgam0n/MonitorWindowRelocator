@echo off
python "%~dp0main.py" --gather
ping 127.0.0.1 -n 3 > nul

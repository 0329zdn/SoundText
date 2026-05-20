@echo off
chcp 65001 >nul
set PYTHONPATH=%~dp0python\Lib\site-packages
set TCL_LIBRARY=%~dp0python\tcl\tcl8.6
set TK_LIBRARY=%~dp0python\tcl\tk8.6
"%~dp0python\python.exe" "%~dp0app.py"
pause
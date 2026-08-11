@echo off
REM COC Bot launcher - double-click this file, or run "run" from a terminal.

REM Always run from the project root so data\loot_data.json resolves correctly.
cd /d "%~dp0"

set PY=py -3.12
%PY% -V >nul 2>&1
if errorlevel 1 (
    echo Python 3.12 not found ^(tried "py -3.12"^), falling back to "python".
    set PY=python
)

REM Install requirements on first run / after a dependency is added.
%PY% -c "import pynput, pyautogui, numpy, PIL, easyocr" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    %PY% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Dependency install failed. Fix the errors above and try again.
        pause
        exit /b 1
    )
)

REM Start the GUI. For the old terminal-only mode, run: py -3.12 src\listener.py
%PY% src\gui.py

REM Keep the window open if the bot crashed or exited, so the error is readable.
echo.
echo Bot stopped.
pause

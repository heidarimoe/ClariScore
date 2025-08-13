@echo off
REM Runs ClariScore processing using your venv and local files
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo ❌ Could not find .venv\Scripts\python.exe
    echo Make sure you created the virtual environment and installed requirements.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m clariscore.scripts.process_input ^
    --benchmarks "ClariScore_Data.xlsx" ^
    --input "ClariScore_Input_Template.xlsx" ^
    --out "ClariScore_Results.xlsx"
echo ✅ Done. Output: ClariScore_Results.xlsx
pause
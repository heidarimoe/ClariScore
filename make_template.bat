@echo off
REM Creates a fresh input template
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo ❌ Could not find .venv\Scripts\python.exe
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m clariscore.scripts.make_input_template ^
  --benchmarks "ClariScore_Data.xlsx" ^
  --out "ClariScore_Input_Template.xlsx"
echo ✅ Template written: ClariScore_Input_Template.xlsx
pause
@echo off
setlocal EnableExtensions
set "SRC=%~dp0"
set "DST=%USERPROFILE%\.agents\skills\codex-claude-debate"
if not exist "%SRC%SKILL.md" (
  echo ERROR: SKILL.md not found. Extract the ZIP first.
  pause
  exit /b 1
)
if not exist "%DST%\scripts" mkdir "%DST%\scripts"
if errorlevel 1 (
  echo ERROR: Cannot create destination folder.
  pause
  exit /b 1
)
copy /Y "%SRC%SKILL.md" "%DST%\SKILL.md" >nul
if errorlevel 1 goto :failed
copy /Y "%SRC%scripts\claude_bridge.py" "%DST%\scripts\claude_bridge.py" >nul
if errorlevel 1 goto :failed
copy /Y "%SRC%README_zh.md" "%DST%\README_zh.md" >nul
if errorlevel 1 goto :failed
echo.
echo INSTALLED: %DST%
echo Restart Codex if the skill is not detected.
echo You can invoke the skill as: codex-claude-debate
echo.
pause
exit /b 0
:failed
echo ERROR: Could not copy one or more files.
pause
exit /b 1

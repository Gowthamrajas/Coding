@echo off
setlocal
set "SCRIPT=%~dp0run-prompt-guard.py"

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3 "%SCRIPT%" <&0
  exit /b %ERRORLEVEL%
)

where python >nul 2>&1
if %ERRORLEVEL%==0 (
  python "%SCRIPT%" <&0
  exit /b %ERRORLEVEL%
)

rem Python not found — fail open so chat still works
echo {"continue": true}
exit /b 0

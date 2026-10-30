@echo off
setlocal
title Institutional Transformation Portfolio
cd /d "%~dp0"
set "VAULT_PYTHON="

echo.
echo Institutional Transformation Portfolio
echo --------------------------------------
echo Finding a working Python environment...

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys; raise SystemExit(sys.version_info < (3, 11))" >nul 2>&1
  if not errorlevel 1 set "VAULT_PYTHON=.venv\Scripts\python.exe"
)
if defined VAULT_PYTHON goto install

if exist "..\.venv\Scripts\python.exe" (
  "..\.venv\Scripts\python.exe" -c "import sys; raise SystemExit(sys.version_info < (3, 11))" >nul 2>&1
  if not errorlevel 1 set "VAULT_PYTHON=..\.venv\Scripts\python.exe"
)
if defined VAULT_PYTHON goto install

if exist "..\.runtime_venv\Scripts\python.exe" (
  "..\.runtime_venv\Scripts\python.exe" -c "import sys; raise SystemExit(sys.version_info < (3, 11))" >nul 2>&1
  if not errorlevel 1 set "VAULT_PYTHON=..\.runtime_venv\Scripts\python.exe"
)
if defined VAULT_PYTHON goto install

if not exist ".runtime_venv\Scripts\python.exe" (
  py -3.12 -m venv .runtime_venv
  if errorlevel 1 py -3.11 -m venv .runtime_venv
  if errorlevel 1 py -m venv .runtime_venv
  if errorlevel 1 python -m venv .runtime_venv
)
set "VAULT_PYTHON=.runtime_venv\Scripts\python.exe"
"%VAULT_PYTHON%" -c "import sys; raise SystemExit(sys.version_info < (3, 11))" >nul 2>&1
if errorlevel 1 (
  echo A working Python installation could not be found.
  echo Install Python 3.11 or newer, then run this launcher again.
  pause
  exit /b 1
)

:install
echo Checking application packages...
"%VAULT_PYTHON%" -c "from importlib.metadata import version; mm=lambda name: tuple(int(part) for part in version(name).split('.')[:2]); assert (1,64) <= mm('streamlit') < (2,0) and (2,2) <= mm('pandas') < (3,0) and (5,5) <= mm('altair') < (7,0)" >nul 2>&1
if errorlevel 1 (
  echo Installing the required packages. This is needed only on first launch...
  "%VAULT_PYTHON%" -m pip install --disable-pip-version-check -r requirements.txt
  if errorlevel 1 (
    echo.
    echo Dependency installation failed. Review the message above and try again.
    pause
    exit /b 1
  )
) else (
  echo Required packages are ready.
)

if not defined VAULT_PORT (
  for /f "delims=" %%P in ('%VAULT_PYTHON% -c "import socket; print(next(port for port in range(8501, 8600) if socket.socket().connect_ex(('127.0.0.1', port))))"') do set "VAULT_PORT=%%P"
)
if not defined VAULT_PORT set "VAULT_PORT=8501"
if not defined VAULT_OPEN_BROWSER set "VAULT_OPEN_BROWSER=true"
echo.
echo Starting the current project from:
echo %CD%
echo Local URL: http://localhost:%VAULT_PORT%
echo Your browser should open automatically at this address.
echo If it does not, copy the Local URL into Edge or Chrome.
echo Keep this window open while using the portfolio.
echo Press Ctrl+C here when you want to stop it.
echo.

if /i "%VAULT_OPEN_BROWSER%"=="true" (
  start "" "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -WindowStyle Hidden -Command "$url='http://localhost:%VAULT_PORT%'; for($attempt=0; $attempt -lt 30; $attempt++){ try { $null=Invoke-WebRequest -UseBasicParsing ($url + '/_stcore/health') -TimeoutSec 1; Start-Process $url; exit } catch { Start-Sleep -Seconds 1 } }"
)

"%VAULT_PYTHON%" -m streamlit run app.py --server.port=%VAULT_PORT% --server.headless=true
set "VAULT_EXIT=%ERRORLEVEL%"
if not "%VAULT_EXIT%"=="0" (
  echo.
  echo The portfolio stopped with an error. Review the message above.
  pause
)
endlocal & exit /b %VAULT_EXIT%

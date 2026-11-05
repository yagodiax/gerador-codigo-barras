@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 main.py
  exit /b %errorlevel%
)
where python >nul 2>nul
if %errorlevel%==0 (
  python main.py
  exit /b %errorlevel%
)
echo Python nao foi encontrado.
echo Para desenvolvimento, instale Python 3.11+.
echo A versao final sera empacotada em .exe e nao exigira Python.
pause

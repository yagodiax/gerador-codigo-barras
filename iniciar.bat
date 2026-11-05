@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PY="
where py.exe >nul 2>nul && (py -3.13 --version >nul 2>nul && set "PY=py")
if not defined PY (
 for /f "delims=" %%P in ('where python.exe 2^>nul') do if not defined PY ("%%P" --version >nul 2>nul && set "PY=%%P")
)
if not defined PY (
 echo Python nao encontrado. Tentando instalar Python 3.13 via WinGet...
 where winget.exe >nul 2>nul || (echo WinGet indisponivel. Instale Python 3.13 manualmente.& pause & exit /b 1)
 winget install --id Python.Python.3.13 --exact --scope user --silent --accept-package-agreements --accept-source-agreements
 if errorlevel 1 (echo Falha na instalacao do Python.& pause & exit /b 1)
 for /d %%D in ("%LocalAppData%\Programs\Python\Python313*") do if exist "%%~fD\python.exe" set "PY=%%~fD\python.exe"
)
if not defined PY (echo Python instalado. Feche e abra este arquivo novamente.& pause& exit /b 1)
if "%PY%"=="py" (py -3.13 -m pip install -r requirements.txt && py -3.13 main.py) else ("%PY%" -m pip install -r requirements.txt && "%PY%" main.py)
if errorlevel 1 pause
endlocal

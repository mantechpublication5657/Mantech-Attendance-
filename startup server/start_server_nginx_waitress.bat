@echo off

echo =========================================
echo      Starting Nginx Server...
echo =========================================

cd /d C:\nginx-1.20.2

start nginx.exe

timeout /t 2 >nul

echo =========================================
echo      Starting Django Waitress Server...
echo =========================================

cd /d "C:\Users\Mantech PC_6\Documents\mantech_hrms_29"

call venv\Scripts\activate

echo =========================================
echo   ManTech HRMS Server Running
echo   Access URL:
echo   http://192.168.1.7
echo =========================================

waitress-serve --host=0.0.0.0 --port=4000 --threads=8 --connection-limit=50 --channel-timeout=60 core.wsgi:application

pause
@echo off

cd /d C:\Users\Mantech PC_6\Documents\mantech_hrms_29

call venv\Scripts\activate

echo =========================================
echo   ManTech HRMS Server Starting...
echo   URL: http://0.0.0.0:4000
echo =========================================

waitress-serve --host=0.0.0.0 --port=4000 --threads=8 --connection-limit=50 --channel-timeout=60 core.wsgi:application

pause
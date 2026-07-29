@echo off
echo ========================================
echo    AUTO MARK MISSING ATTENDANCE
echo ========================================
echo.

cd /d "C:\Users\Mantech PC_6\Documents\mantech_hrms_29"

echo Running mark missing attendance...
"C:\Users\Mantech PC_6\AppData\Local\Programs\Python\Python311\python.exe" manage.py mark_missing_attendance

echo.
echo Attendance marking completed.
echo ========================================
pause
@echo off
echo ========================================
echo    AUTO PAYROLL CREATION
echo ========================================
echo.

cd /d "C:\Users\Mantech PC_6\Documents\mantech_hrms_29"

echo Running auto payroll creation...
"C:\Users\Mantech PC_6\AppData\Local\Programs\Python\Python311\python.exe" manage.py auto_create_payroll

echo.
echo Payroll creation completed.
echo ========================================
pause
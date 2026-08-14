@echo off
echo ========================================
echo   REGISTRU TRANSFERURI MEDIA v2.0
echo ========================================
echo.

echo [1/2] Verificare Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo EROARE: Python nu este instalat!
    echo Descarca Python de la: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [2/2] Pornire aplicatie...
python main.py

pause

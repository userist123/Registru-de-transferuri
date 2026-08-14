@echo off
echo ============================================
echo  Registru Transferuri Media v3.1
echo ============================================
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python nu este instalat sau nu este in PATH.
    pause
    exit /b 1
)
pip install -r requirements.txt --quiet
python main.py
pause

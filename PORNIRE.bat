@echo off
title Registru Transferuri Media v3.0
echo Verificare Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python nu este instalat sau nu este in PATH!
    pause
    exit /b
)
echo Pornire aplicatie Registru Transferuri Media v3.0...
python main.py
pause

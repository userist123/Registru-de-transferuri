@echo off
:: Script de deblocare si resetare totala a politicilor USB / Storage
:: Solicita automat drepturi de Administrator (UAC)

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Solicitare drepturi de Administrator pentru stergerea politicilor GPO...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo =======================================================
echo   DEBLOCARE SI RESTABILIRE ACCES MEDII DE STOCARE USB
echo =======================================================
echo.

echo [1/4] Stergere politici GPO RemovableStorageDevices (Deny_All / Deny_Read / Deny_Write)...
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows\RemovableStorageDevices" /f >nul 2>&1
reg delete "HKCU\SOFTWARE\Policies\Microsoft\Windows\RemovableStorageDevices" /f >nul 2>&1

echo [2/4] Stergere StorageDevicePolicies (WriteProtect)...
reg delete "HKLM\SYSTEM\CurrentControlSet\Control\StorageDevicePolicies" /f >nul 2>&1

echo [3/4] Resetare serviciu USBSTOR la valoarea normala (Start=3)...
reg add "HKLM\SYSTEM\CurrentControlSet\Services\USBSTOR" /v "Start" /t REG_DWORD /d 3 /f >nul 2>&1

echo [4/4] Actualizare politici Windows (gpupdate)...
gpupdate /force >nul 2>&1

echo.
echo =======================================================
echo   SUCCES! Toate politicile au fost sterse cu succes.
echo   Accesul la mediile de stocare USB a fost deblocat.
echo =======================================================
echo.
pause

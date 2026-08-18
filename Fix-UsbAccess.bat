@echo off
:: Script de deblocare si resetare totala a politicilor USB / Storage
:: Deschide automat cu drepturi de Administrator

cd /d "%~dp0"

echo =======================================================
echo   DEBLOCARE SI RESTABILIRE ACCES MEDII DE STOCARE USB
echo =======================================================
echo.

echo [1/3] Import fisier registru Unlock-Usb.reg...
reg import Unlock-Usb.reg >nul 2>&1
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows\RemovableStorageDevices" /f >nul 2>&1
reg delete "HKCU\SOFTWARE\Policies\Microsoft\Windows\RemovableStorageDevices" /f >nul 2>&1
reg delete "HKLM\SYSTEM\CurrentControlSet\Control\StorageDevicePolicies" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\USBSTOR" /v "Start" /t REG_DWORD /d 3 /f >nul 2>&1

echo [2/3] Fortare actualizare politici de grup (gpupdate)...
gpupdate /force

echo [3/3] Activare montare automata a unitatilor (mountvol)...
mountvol /E >nul 2>&1

echo.
echo =======================================================
echo   SUCCES! Politicile Windows au fost eliminate.
echo   Deconecteaza si reconecteaza stick-ul USB in port.
echo =======================================================
echo.
pause

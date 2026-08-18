@echo off
:: Script de Resetare Totala si Definitiva a Politicilor GPO & USB
:: Solicita automat drepturi de Administrator

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Solicitare drepturi de Administrator...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ====================================================================
echo   RESETARE DEFINITIVA GPO & DEBLOCARE COMPLETA MEDII DE STOCARE USB
echo ====================================================================
echo.

echo [1/5] Stergere fisiere locale Group Policy (Registry.pol)...
del /f /q "%SystemRoot%\System32\GroupPolicy\Machine\Registry.pol" >nul 2>&1
del /f /q "%SystemRoot%\System32\GroupPolicy\User\Registry.pol" >nul 2>&1

echo [2/5] Stergere chei de registru RemovableStorageDevices si StorageDevicePolicies...
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows\RemovableStorageDevices" /f >nul 2>&1
reg delete "HKCU\SOFTWARE\Policies\Microsoft\Windows\RemovableStorageDevices" /f >nul 2>&1
reg delete "HKLM\SYSTEM\CurrentControlSet\Control\StorageDevicePolicies" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\USBSTOR" /v "Start" /t REG_DWORD /d 3 /f >nul 2>&1

echo [3/5] Aplicare actualizare politici curate (gpupdate /force)...
gpupdate /force

echo [4/5] Activare Automount pentru recunoastere automata partitii...
mountvol /E >nul 2>&1

echo [5/5] Rescanare magistrala hardware PnP...
pnputil /scan-devices >nul 2>&1

echo.
echo ====================================================================
echo   SUCCES TOTAL! Fisierele GPO si restrictiile au fost eliminate.
echo   Deconecteaza si reconecteaza stick-ul USB (DataTraveler).
echo ====================================================================
echo.
pause

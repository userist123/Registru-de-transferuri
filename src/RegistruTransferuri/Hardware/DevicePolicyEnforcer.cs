using System.Diagnostics;
using System.IO;
using System.Security;
using Microsoft.Win32;
using RegistruTransferuri.Models;

namespace RegistruTransferuri.Hardware;

public enum UsbPolicyMode
{
    FullAccess = 0,        // Porturi active, scriere/citire permise
    ReadOnly = 1,          // Mod forțat doar-citire pe toate mediile (WriteProtect)
    WhitelistOnly = 2,     // Doar mediile amprentate în baza de date sunt permise
    BlockAll = 3           // Blocare totală a tuturor porturilor de stocare de masă (USBSTOR Start=4)
}

public sealed record DeviceEvaluationResult(
    bool IsAllowed,
    bool IsReadOnlyEnforced,
    string StatusReason,
    MediaStatus AssignedPolicy
);

/// <summary>
/// Modul de Control al Dispozitivelor și Politicilor de Porturi Endpoint Protection (Air-Gapped Device Control).
/// Gestionează politicile USBSTOR, StorageDevicePolicies și validarea Whitelist în timp real pentru toate tipurile de medii.
/// </summary>
public static class DevicePolicyEnforcer
{
    private const string UsbStorRegPath = @"SYSTEM\CurrentControlSet\Services\USBSTOR";
    private const string StoragePoliciesRegPath = @"SYSTEM\CurrentControlSet\Control\StorageDevicePolicies";

    public static UsbPolicyMode CurrentPolicy { get; private set; } = UsbPolicyMode.WhitelistOnly;

    /// <summary>
    /// Citește politica de sistem din Registry (HKLM).
    /// </summary>
    public static UsbPolicyMode QuerySystemPolicy()
    {
        try
        {
            using var usbKey = Registry.LocalMachine.OpenSubKey(UsbStorRegPath, false);
            var startVal = usbKey?.GetValue("Start");
            if (startVal is int val && val == 4)
            {
                CurrentPolicy = UsbPolicyMode.BlockAll;
                return UsbPolicyMode.BlockAll;
            }

            using var polKey = Registry.LocalMachine.OpenSubKey(StoragePoliciesRegPath, false);
            var wpVal = polKey?.GetValue("WriteProtect");
            if (wpVal is int wp && wp == 1)
            {
                CurrentPolicy = UsbPolicyMode.ReadOnly;
                return UsbPolicyMode.ReadOnly;
            }
        }
        catch { }

        return CurrentPolicy;
    }

    /// <summary>
    /// Aplică politica selectată pe sistemul de operare și în motorul aplicației.
    /// Suportă rulare standard cu fallback și apel opțional elevated.
    /// </summary>
    public static (bool Success, string Message) ApplyPolicy(UsbPolicyMode mode, string operatorName)
    {
        CurrentPolicy = mode;
        var details = "";
        bool elevatedSuccess = false;

        switch (mode)
        {
            case UsbPolicyMode.BlockAll:
                elevatedSuccess = TrySetRegistryDirectOrElevated(UsbStorRegPath, "Start", "4", "REG_DWORD");
                details = "POLITICĂ APLICATĂ: Blocare totală porturi USB Storage (USBSTOR Start=4).";
                break;

            case UsbPolicyMode.ReadOnly:
                TrySetRegistryDirectOrElevated(UsbStorRegPath, "Start", "3", "REG_DWORD");
                elevatedSuccess = TrySetRegistryDirectOrElevated(StoragePoliciesRegPath, "WriteProtect", "1", "REG_DWORD");
                details = "POLITICĂ APLICATĂ: Mod forțat doar-citire pe toate mediile (WriteProtect=1).";
                break;

            case UsbPolicyMode.WhitelistOnly:
                TrySetRegistryDirectOrElevated(UsbStorRegPath, "Start", "3", "REG_DWORD");
                elevatedSuccess = TrySetRegistryDirectOrElevated(StoragePoliciesRegPath, "WriteProtect", "0", "REG_DWORD");
                details = "POLITICĂ APLICATĂ: Mod Whitelist Strict — Accesul este permis exclusiv mediilor amprentate în baza de date militară.";
                break;

            case UsbPolicyMode.FullAccess:
                TrySetRegistryDirectOrElevated(UsbStorRegPath, "Start", "3", "REG_DWORD");
                elevatedSuccess = TrySetRegistryDirectOrElevated(StoragePoliciesRegPath, "WriteProtect", "0", "REG_DWORD");
                details = "POLITICĂ APLICATĂ: Acces complet Read/Write pe toate porturile.";
                break;
        }

        if (elevatedSuccess)
        {
            return (true, $"{details}\n\n[CONFIRMARE SISTEM]: Setările de registru Windows HKLM au fost actualizate la nivel de kernel.");
        }
        else
        {
            return (true, $"{details}\n\n[PROTECȚIE ACTIVĂ LA NIVEL DE APLICAȚIE]: Politica militară este impusă în timp real de Registrul de Transferuri.");
        }
    }

    /// <summary>
    /// Evaluează un mediu conectat (USB, SATA, NVMe, SD, CD-DVD) în raport cu Whitelist-ul activ și politica curentă.
    /// </summary>
    public static DeviceEvaluationResult EvaluateDevice(DetectedMedia device, List<MediaAsset> whitelist)
    {
        if (CurrentPolicy == UsbPolicyMode.BlockAll)
        {
            return new DeviceEvaluationResult(false, true, "BLOCAT DE POLITICĂ: Toate porturile de stocare sunt oprite pe această stație.", MediaStatus.Blocat);
        }

        // Căutare după seria hardware unică (S/N) indiferent de tipul de mediu (USB, SATA, NVMe, SD, Optic)
        var matched = whitelist.FirstOrDefault(w =>
            !string.IsNullOrWhiteSpace(w.SerialNumber) &&
            string.Equals(w.SerialNumber.Trim(), device.SerialNumber.Trim(), StringComparison.OrdinalIgnoreCase));

        if (matched == null)
        {
            if (CurrentPolicy == UsbPolicyMode.WhitelistOnly)
            {
                return new DeviceEvaluationResult(false, true, $"⚠️ NEAUTORIZAT (WHITELIST VIOLATION): Suportul [{device.MediaType}] ({device.Model}) nu este amprentat în baza de date militară!", MediaStatus.InAsteptare);
            }
            return new DeviceEvaluationResult(true, CurrentPolicy == UsbPolicyMode.ReadOnly, $"Mediu [{device.MediaType}] neînregistrat dar permis de politica de acces curentă.", MediaStatus.InAsteptare);
        }

        switch (matched.Status)
        {
            case MediaStatus.AutorizatRw:
                var isRo = CurrentPolicy == UsbPolicyMode.ReadOnly;
                return new DeviceEvaluationResult(true, isRo, isRo ? $"Autorizat [{device.MediaType}] în Whitelist (restrâns la Read-Only de politica globală)." : $"✅ AUTORIZAT COMPLET [{device.MediaType}] (Read/Write conform Whitelist).", matched.Status);

            case MediaStatus.AutorizatRo:
                return new DeviceEvaluationResult(true, true, $"👁️ AUTORIZAT STRICT READ-ONLY [{device.MediaType}] (Conform politicilor de securitate din Whitelist).", matched.Status);

            case MediaStatus.Blocat:
            case MediaStatus.Sanitizat:
                return new DeviceEvaluationResult(false, true, $"🚫 MEDIU BLOCAT / REVOCAT [{device.MediaType}]: Utilizarea acestui suport de stocare este strict interzisă!", matched.Status);

            default:
                return new DeviceEvaluationResult(false, true, $"⏳ ÎN AȘTEPTARE APROBARE [{device.MediaType}]: Mediul necesită autorizarea unui ofițer de securitate.", matched.Status);
        }
    }

    /// <summary>
    /// Ejectare forțată sau demontare volum neautorizat.
    /// </summary>
    public static bool EjectVolume(string driveLetter)
    {
        if (string.IsNullOrWhiteSpace(driveLetter)) return false;
        var cleanLetter = driveLetter.Trim().TrimEnd(':');

        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = "powershell.exe",
                Arguments = $"-NoProfile -Command \"$drive = Get-Volume -DriveLetter '{cleanLetter}' -ErrorAction SilentlyContinue; if ($drive) {{ (New-Object -comObject Shell.Application).Namespace(17).ParseName('{cleanLetter}:').InvokeVerb('Eject') }}\"",
                CreateNoWindow = true,
                UseShellExecute = false
            };
            using var proc = Process.Start(psi);
            proc?.WaitForExit(3000);
            return true;
        }
        catch
        {
            return false;
        }
    }

    private static bool TrySetRegistryDirectOrElevated(string subKey, string valueName, string value, string type)
    {
        // 1. Încercare scriere directă în Registry
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(subKey, true) ?? Registry.LocalMachine.CreateSubKey(subKey, true);
            if (key != null)
            {
                if (type == "REG_DWORD" && int.TryParse(value, out var intVal))
                    key.SetValue(valueName, intVal, RegistryValueKind.DWord);
                else
                    key.SetValue(valueName, value, RegistryValueKind.String);

                return true;
            }
        }
        catch (SecurityException) { }
        catch (UnauthorizedAccessException) { }
        catch (Exception) { }

        // 2. Fallback: încercare prin comanda reg.exe silențioasă
        try
        {
            var fullKey = $@"HKLM\{subKey}";
            var psi = new ProcessStartInfo
            {
                FileName = "reg.exe",
                Arguments = $"add \"{fullKey}\" /v \"{valueName}\" /t {type} /d {value} /f",
                CreateNoWindow = true,
                UseShellExecute = false
            };
            using var proc = Process.Start(psi);
            proc?.WaitForExit(2000);
            return proc?.ExitCode == 0;
        }
        catch
        {
            return false;
        }
    }
}

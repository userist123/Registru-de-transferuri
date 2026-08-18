using System.Diagnostics;
using System.IO;
using System.Security;
using Microsoft.Win32;
using RegistruTransferuri.Models;

namespace RegistruTransferuri.Hardware;

public enum UsbPolicyMode
{
    FullAccess = 0,        // Fără restricții, acces complet Read/Write pe toate mediile
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
/// Modul de Control al Dispozitivelor și Politicilor de Porturi Endpoint Protection.
/// Asigură aplicarea și eliminarea sigură a restricțiilor fără a bloca accesul legitim la medii.
/// </summary>
public static class DevicePolicyEnforcer
{
    private const string UsbStorRegPath = @"SYSTEM\CurrentControlSet\Services\USBSTOR";
    private const string StoragePoliciesRegPath = @"SYSTEM\CurrentControlSet\Control\StorageDevicePolicies";
    private const string GpoPoliciesRegPath = @"SOFTWARE\Policies\Microsoft\Windows\RemovableStorageDevices";

    public static UsbPolicyMode CurrentPolicy { get; private set; } = UsbPolicyMode.FullAccess;

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
    /// </summary>
    public static (bool Success, string Message) ApplyPolicy(UsbPolicyMode mode, string operatorName)
    {
        CurrentPolicy = mode;
        var details = "";

        switch (mode)
        {
            case UsbPolicyMode.BlockAll:
                TrySetRegistryDirectOrElevated(UsbStorRegPath, "Start", "4", "REG_DWORD");
                details = "POLITICĂ APLICATĂ: Blocare totală porturi USB Storage (USBSTOR Start=4).";
                break;

            case UsbPolicyMode.ReadOnly:
                TrySetRegistryDirectOrElevated(UsbStorRegPath, "Start", "3", "REG_DWORD");
                TrySetRegistryDirectOrElevated(StoragePoliciesRegPath, "WriteProtect", "1", "REG_DWORD");
                details = "POLITICĂ APLICATĂ: Mod forțat doar-citire pe toate mediile (WriteProtect=1).";
                break;

            case UsbPolicyMode.WhitelistOnly:
                TrySetRegistryDirectOrElevated(UsbStorRegPath, "Start", "3", "REG_DWORD");
                TryDeleteRegistryKeyDirectOrElevated(StoragePoliciesRegPath);
                details = "POLITICĂ APLICATĂ: Mod Whitelist Strict — Accesul este permis exclusiv mediilor amprentate în baza de date militară.";
                break;

            case UsbPolicyMode.FullAccess:
                return RemoveAllPolicies(operatorName);
        }

        return (true, $"{details}\n\nProtecția este activă pe stație.");
    }

    /// <summary>
    /// Elimină complet toate politicile de blocare și restricțiile, readucând sistemul la starea implicită de acces neîngrădit.
    /// </summary>
    public static (bool Success, string Message) RemoveAllPolicies(string operatorName)
    {
        CurrentPolicy = UsbPolicyMode.FullAccess;

        // 1. Resetare USBSTOR Start = 3 (activare completă)
        TrySetRegistryDirectOrElevated(UsbStorRegPath, "Start", "3", "REG_DWORD");

        // 2. Ștergere completă a cheii StorageDevicePolicies (elimină WriteProtect și Access Denied)
        TryDeleteRegistryKeyDirectOrElevated(StoragePoliciesRegPath);

        // 3. Ștergere politici GPO locale dacă au fost scrise
        TryDeleteRegistryKeyDirectOrElevated(GpoPoliciesRegPath);

        // 4. Re-activare Automount și notificare sistem
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = "/c mountvol /E",
                CreateNoWindow = true,
                UseShellExecute = false
            };
            using var p = Process.Start(psi);
            p?.WaitForExit(1000);
        }
        catch { }

        return (true, "TOATE RESTRICȚIILE ȘI POLITICILE AU FOST ANULATE COMPLET:\n\n" +
                      "✅ Porturile USB sunt deblocate (USBSTOR Start=3).\n" +
                      "✅ Protecția la scriere (WriteProtect) a fost eliminată.\n" +
                      "✅ Toate mediile de stocare au acces deplin Read/Write.");
    }

    /// <summary>
    /// Evaluează un mediu conectat (USB, SATA, NVMe, SD, CD-DVD) în raport cu Whitelist-ul activ și politica curentă.
    /// </summary>
    public static DeviceEvaluationResult EvaluateDevice(DetectedMedia device, List<MediaAsset> whitelist)
    {
        // CÂND POLITICILE SUNT SCOASE (FullAccess) -> ACCESUL ESTE LIBER PENTRU ORICE MEDIU
        if (CurrentPolicy == UsbPolicyMode.FullAccess)
        {
            return new DeviceEvaluationResult(true, false, "✅ ACCES COMPLET AUTORIZAT (Politici dezactivate - Regim Normal)", MediaStatus.AutorizatRw);
        }

        if (CurrentPolicy == UsbPolicyMode.BlockAll)
        {
            return new DeviceEvaluationResult(false, true, "BLOCAT DE POLITICĂ: Toate porturile de stocare sunt oprite pe această stație.", MediaStatus.Blocat);
        }

        // Căutare după seria hardware unică (S/N)
        var matched = whitelist.FirstOrDefault(w =>
            !string.IsNullOrWhiteSpace(w.SerialNumber) &&
            string.Equals(w.SerialNumber.Trim(), device.SerialNumber.Trim(), StringComparison.OrdinalIgnoreCase));

        if (matched == null)
        {
            if (CurrentPolicy == UsbPolicyMode.WhitelistOnly)
            {
                return new DeviceEvaluationResult(false, true, $"⚠️ NEAUTORIZAT (WHITELIST VIOLATION): Suportul [{device.MediaType}] ({device.Model}) nu este amprentat în baza de date militară!", MediaStatus.InAsteptare);
            }
            return new DeviceEvaluationResult(true, CurrentPolicy == UsbPolicyMode.ReadOnly, $"Mediu [{device.MediaType}] neînregistrat dar permis de politica curentă.", MediaStatus.InAsteptare);
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
        catch { }

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
            proc?.WaitForExit(1500);
            return proc?.ExitCode == 0;
        }
        catch
        {
            return false;
        }
    }

    private static bool TryDeleteRegistryKeyDirectOrElevated(string subKey)
    {
        try
        {
            Registry.LocalMachine.DeleteSubKeyTree(subKey, false);
            return true;
        }
        catch { }

        try
        {
            var fullKey = $@"HKLM\{subKey}";
            var psi = new ProcessStartInfo
            {
                FileName = "reg.exe",
                Arguments = $"delete \"{fullKey}\" /f",
                CreateNoWindow = true,
                UseShellExecute = false
            };
            using var proc = Process.Start(psi);
            proc?.WaitForExit(1500);
            return proc?.ExitCode == 0;
        }
        catch
        {
            return false;
        }
    }
}

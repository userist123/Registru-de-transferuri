using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using Microsoft.Win32;
using RegistruTransferuri.Models;

namespace RegistruTransferuri.Hardware;

public enum UsbPolicyMode
{
    FullAccess = 0,        // Porturi active, scriere/citire permise
    ReadOnly = 1,          // Mod forțat doar-citire pe toate mediile USB (WriteProtect)
    WhitelistOnly = 2,     // Doar mediile amprentate în baza de date sunt permise
    BlockAll = 3           // Blocare totală a tuturor porturilor USB Storage (USBSTOR Start=4)
}

public sealed record DeviceEvaluationResult(
    bool IsAllowed,
    bool IsReadOnlyEnforced,
    string StatusReason,
    MediaStatus AssignedPolicy
);

/// <summary>
/// Modul de Control al Dispozitivelor si Politicilor de Porturi Endpoint Protection (Air-Gapped Device Control).
/// Gestioneaza politicile USBSTOR, StorageDevicePolicies si validarea Whitelist in timp real.
/// </summary>
public static class DevicePolicyEnforcer
{
    private const string UsbStorRegPath = @"SYSTEM\CurrentControlSet\Services\USBSTOR";
    private const string StoragePoliciesRegPath = @"SYSTEM\CurrentControlSet\Control\StorageDevicePolicies";

    public static UsbPolicyMode CurrentPolicy { get; private set; } = UsbPolicyMode.WhitelistOnly;

    /// <summary>
    /// Citeste politica de sistem din Registry.
    /// </summary>
    public static UsbPolicyMode QuerySystemPolicy()
    {
        try
        {
            using var usbKey = Registry.LocalMachine.OpenSubKey(UsbStorRegPath);
            var startVal = usbKey?.GetValue("Start");
            if (startVal is int val && val == 4)
            {
                CurrentPolicy = UsbPolicyMode.BlockAll;
                return UsbPolicyMode.BlockAll;
            }

            using var polKey = Registry.LocalMachine.OpenSubKey(StoragePoliciesRegPath);
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
    /// Aplica politica selectata pe sistemul de operare.
    /// </summary>
    public static (bool Success, string Message) ApplyPolicy(UsbPolicyMode mode, string operatorName)
    {
        CurrentPolicy = mode;
        var details = "";

        try
        {
            switch (mode)
            {
                case UsbPolicyMode.BlockAll:
                    SetRegistryValue(Registry.LocalMachine, UsbStorRegPath, "Start", 4, RegistryValueKind.DWord);
                    details = "POLITICĂ APLICATĂ: Blocare totală porturi USB Storage (USBSTOR Start=4).";
                    break;

                case UsbPolicyMode.ReadOnly:
                    SetRegistryValue(Registry.LocalMachine, UsbStorRegPath, "Start", 3, RegistryValueKind.DWord);
                    EnsureStorageDevicePoliciesKey();
                    SetRegistryValue(Registry.LocalMachine, StoragePoliciesRegPath, "WriteProtect", 1, RegistryValueKind.DWord);
                    details = "POLITICĂ APLICATĂ: Mod forțat doar-citire pe toate unitățile USB (WriteProtect=1).";
                    break;

                case UsbPolicyMode.WhitelistOnly:
                    SetRegistryValue(Registry.LocalMachine, UsbStorRegPath, "Start", 3, RegistryValueKind.DWord);
                    EnsureStorageDevicePoliciesKey();
                    SetRegistryValue(Registry.LocalMachine, StoragePoliciesRegPath, "WriteProtect", 0, RegistryValueKind.DWord);
                    details = "POLITICĂ APLICATĂ: Mod Whitelist Strict — Accesul este permis exclusiv mediilor amprentate în baza de date.";
                    break;

                case UsbPolicyMode.FullAccess:
                    SetRegistryValue(Registry.LocalMachine, UsbStorRegPath, "Start", 3, RegistryValueKind.DWord);
                    EnsureStorageDevicePoliciesKey();
                    SetRegistryValue(Registry.LocalMachine, StoragePoliciesRegPath, "WriteProtect", 0, RegistryValueKind.DWord);
                    details = "POLITICĂ APLICATĂ: Acces complet Read/Write pe toate porturile USB.";
                    break;
            }

            return (true, details);
        }
        catch (UnauthorizedAccessException)
        {
            // Dacă aplicația nu rulează ca Administrator complet, politica logică Whitelist rămâne activă la nivel de aplicație
            return (true, $"[Avertisment UAC: Setare Registry simulată logic] {details} (Necesită drepturi administrative pentru scriere în HKLM)");
        }
        catch (Exception ex)
        {
            return (false, $"Eroare la aplicarea politicii: {ex.Message}");
        }
    }

    /// <summary>
    /// Evalueaza un mediu conectat in raport cu Whitelist-ul activ si politica curenta.
    /// </summary>
    public static DeviceEvaluationResult EvaluateDevice(DetectedMedia device, List<MediaAsset> whitelist)
    {
        if (CurrentPolicy == UsbPolicyMode.BlockAll)
        {
            return new DeviceEvaluationResult(false, true, "BLOCAT DE POLITICĂ: Toate porturile USB sunt oprite pe această stație.", MediaStatus.Blocat);
        }

        // Căutare după seria hardware unică (S/N)
        var matched = whitelist.FirstOrDefault(w =>
            string.Equals(w.SerialNumber.Trim(), device.SerialNumber.Trim(), StringComparison.OrdinalIgnoreCase));

        if (matched == null)
        {
            if (CurrentPolicy == UsbPolicyMode.WhitelistOnly)
            {
                return new DeviceEvaluationResult(false, true, "⚠️ NEAUTORIZAT (WHITELIST VIOLATION): Acest mediu nu este înregistrat în baza de date militară!", MediaStatus.InAsteptare);
            }
            return new DeviceEvaluationResult(true, CurrentPolicy == UsbPolicyMode.ReadOnly, "Mediu neînregistrat dar permis de politica de acces curentă.", MediaStatus.InAsteptare);
        }

        switch (matched.Status)
        {
            case MediaStatus.AutorizatRw:
                var isRo = CurrentPolicy == UsbPolicyMode.ReadOnly;
                return new DeviceEvaluationResult(true, isRo, isRo ? "Autorizat în Whitelist (restrâns la Read-Only de politica globală)." : "✅ AUTORIZAT COMPLET (Read/Write conform Whitelist).", matched.Status);

            case MediaStatus.AutorizatRo:
                return new DeviceEvaluationResult(true, true, "👁️ AUTORIZAT STRICT READ-ONLY (Conform politicilor de securitate din Whitelist).", matched.Status);

            case MediaStatus.Blocat:
            case MediaStatus.Sanitizat:
                return new DeviceEvaluationResult(false, true, "🚫 MEDIU BLOCAT / REVOCAT: Utilizarea acestui suport de stocare este strict interzisă!", matched.Status);

            default:
                return new DeviceEvaluationResult(false, true, "⏳ ÎN AȘTEPTARE APROBARE: Mediul necesită autorizarea unui ofițer de securitate.", matched.Status);
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
            // Apel de ejectare via PowerShell nativ
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

    private static void EnsureStorageDevicePoliciesKey()
    {
        try
        {
            using var key = Registry.LocalMachine.CreateSubKey(StoragePoliciesRegPath, true);
        }
        catch { }
    }

    private static void SetRegistryValue(RegistryKey root, string subKey, string valueName, object value, RegistryValueKind kind)
    {
        using var key = root.OpenSubKey(subKey, true) ?? root.CreateSubKey(subKey, true);
        key?.SetValue(valueName, value, kind);
    }
}

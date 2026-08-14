using System.Management;

namespace RegistruTransferuri.Hardware;

/// <summary>Identitate hardware a unui mediu USB detectat prin WMI — nu introdus manual.</summary>
public sealed record DetectedMedia(
    string SerialNumber, string VendorId, string ProductId,
    string Model, long CapacityBytes, string DriveLetter);

/// <summary>
/// Detectare automata a mediilor amovibile prin WMI.
/// Lant: Win32_DiskDrive (InterfaceType='USB') -> Win32_DiskDriveToDiskPartition
/// -> Win32_LogicalDiskToPartition -> Win32_LogicalDisk (litera de montare).
/// Elimina riscul de obfuscare/eroare la introducerea manuala a seriei.
/// </summary>
public static class WmiMediaDetector
{
    public static List<DetectedMedia> DetectUsbMedia()
    {
        var results = new List<DetectedMedia>();
        using var driveSearcher = new ManagementObjectSearcher(
            "SELECT DeviceID, SerialNumber, Model, Size, PNPDeviceID FROM Win32_DiskDrive WHERE InterfaceType='USB'");

        foreach (ManagementObject drive in driveSearcher.Get())
        {
            var deviceId = drive["DeviceID"]?.ToString() ?? "";
            var pnpId = drive["PNPDeviceID"]?.ToString() ?? "";
            var (vid, pid) = ParseVidPid(pnpId);
            var serial = (drive["SerialNumber"]?.ToString() ?? "").Trim();
            var model = drive["Model"]?.ToString() ?? "";
            var size = long.TryParse(drive["Size"]?.ToString(), out var s) ? s : 0L;
            var letter = ResolveDriveLetter(deviceId);
            results.Add(new DetectedMedia(serial, vid, pid, model, size, letter));
        }
        return results;
    }

    private static string ResolveDriveLetter(string deviceId)
    {
        using var partSearcher = new ManagementObjectSearcher(
            $"ASSOCIATORS OF {{Win32_DiskDrive.DeviceID='{deviceId}'}} WHERE AssocClass=Win32_DiskDriveToDiskPartition");
        foreach (ManagementObject part in partSearcher.Get())
        {
            var partId = part["DeviceID"]?.ToString() ?? "";
            using var logSearcher = new ManagementObjectSearcher(
                $"ASSOCIATORS OF {{Win32_DiskPartition.DeviceID='{partId}'}} WHERE AssocClass=Win32_LogicalDiskToPartition");
            foreach (ManagementObject log in logSearcher.Get())
                return log["Name"]?.ToString() ?? "";
        }
        return "";
    }

    private static (string Vid, string Pid) ParseVidPid(string pnpDeviceId)
    {
        string vid = "", pid = "";
        var vidIdx = pnpDeviceId.IndexOf("VID_", StringComparison.OrdinalIgnoreCase);
        if (vidIdx >= 0) vid = pnpDeviceId.Substring(vidIdx + 4, 4);
        var pidIdx = pnpDeviceId.IndexOf("PID_", StringComparison.OrdinalIgnoreCase);
        if (pidIdx >= 0) pid = pnpDeviceId.Substring(pidIdx + 4, 4);
        return (vid, pid);
    }
}

/// <summary>
/// Watcher asincron — eveniment la conectarea/deconectarea unui mediu USB.
/// </summary>
public sealed class UsbWatcher : IDisposable
{
    private readonly ManagementEventWatcher _insertWatcher;
    private readonly ManagementEventWatcher _removeWatcher;

    public event Action? MediaInserted;
    public event Action? MediaRemoved;

    public UsbWatcher()
    {
        var insertQuery = new WqlEventQuery(
            "SELECT * FROM __InstanceCreationEvent WITHIN 1 WHERE TargetInstance ISA 'Win32_DiskDrive'");
        var removeQuery = new WqlEventQuery(
            "SELECT * FROM __InstanceDeletionEvent WITHIN 1 WHERE TargetInstance ISA 'Win32_DiskDrive'");
        _insertWatcher = new ManagementEventWatcher(insertQuery);
        _removeWatcher = new ManagementEventWatcher(removeQuery);
        _insertWatcher.EventArrived += (_, _) => MediaInserted?.Invoke();
        _removeWatcher.EventArrived += (_, _) => MediaRemoved?.Invoke();
    }

    public void Start() { _insertWatcher.Start(); _removeWatcher.Start(); }
    public void Dispose() { _insertWatcher.Stop(); _removeWatcher.Stop(); _insertWatcher.Dispose(); _removeWatcher.Dispose(); }
}

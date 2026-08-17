using System.Management;

namespace RegistruTransferuri.Hardware;

/// <summary>Identitate hardware a unui mediu detectat prin WMI / Windows.</summary>
public sealed record DetectedMedia(
    string SerialNumber,
    string VendorId,
    string ProductId,
    string Manufacturer,
    string Model,
    long CapacityBytes,
    string DriveLetter,
    string MediaType,
    bool IsRemovable,
    bool IsOptical
)
{
    public double CapacityGb => Math.Round((double)CapacityBytes / (1024 * 1024 * 1024), 2);
    public string DisplayLabel => $"{DriveLetter} [{MediaType}] {Manufacturer} {Model} (S/N: {SerialNumber}) — {CapacityGb} GB";
}

/// <summary>
/// Detectare universala a tuturor mediilor conectate (USB, SATA, CD/DVD, SD) prin WMI.
/// </summary>
public static class WmiMediaDetector
{
    public static List<DetectedMedia> DetectAllMedia()
    {
        var results = new List<DetectedMedia>();

        // 1. Scanare Discuri Fizice (USB, SATA, SD)
        try
        {
            using var driveSearcher = new ManagementObjectSearcher(
                "SELECT DeviceID, SerialNumber, Model, Size, PNPDeviceID, InterfaceType, MediaType FROM Win32_DiskDrive");

            foreach (ManagementObject drive in driveSearcher.Get())
            {
                var deviceId = drive["DeviceID"]?.ToString() ?? "";
                var pnpId = drive["PNPDeviceID"]?.ToString() ?? "";
                var iface = drive["InterfaceType"]?.ToString() ?? "USB";
                var (vid, pid, ven, prod) = ParseHardwareIds(pnpId);
                var serial = (drive["SerialNumber"]?.ToString() ?? "").Trim();
                if (string.IsNullOrWhiteSpace(serial)) serial = $"SN-DISK-{Math.Abs(deviceId.GetHashCode()):X8}";

                var model = drive["Model"]?.ToString() ?? "Generic Disk";
                var size = long.TryParse(drive["Size"]?.ToString(), out var s) ? s : 0L;
                var letter = ResolveDriveLetter(deviceId);
                var isRemovable = iface.Equals("USB", StringComparison.OrdinalIgnoreCase) || pnpId.Contains("USBSTOR");
                var medType = isRemovable ? "Stick USB Flash" : (iface.Equals("SCSI", StringComparison.OrdinalIgnoreCase) ? "SSD / NVMe Fix" : "Disc SATA");

                results.Add(new DetectedMedia(serial, vid, pid, ven, model, size, letter, medType, isRemovable, false));
            }
        }
        catch { }

        // 2. Scanare Unități Optice (CD/DVD/BD)
        try
        {
            using var cdSearcher = new ManagementObjectSearcher(
                "SELECT DeviceID, Drive, Name, VolumeName, Size, PNPDeviceID FROM Win32_CDROMDrive");

            foreach (ManagementObject cd in cdSearcher.Get())
            {
                var driveLetter = cd["Drive"]?.ToString() ?? "D:";
                var name = cd["Name"]?.ToString() ?? "Unitate Optică CD/DVD";
                var pnpId = cd["PNPDeviceID"]?.ToString() ?? "";
                var (vid, pid, ven, prod) = ParseHardwareIds(pnpId);
                var serial = $"OPTICAL-{driveLetter.TrimEnd(':')}-{Math.Abs(pnpId.GetHashCode()):X8}";
                var size = long.TryParse(cd["Size"]?.ToString(), out var s) ? s : 4_700_000_000L;

                results.Add(new DetectedMedia(serial, vid, pid, "OpticalDrive", name, size, driveLetter, "Disc Optic CD/DVD", true, true));
            }
        }
        catch { }

        return results;
    }

    private static string ResolveDriveLetter(string deviceId)
    {
        try
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
        }
        catch { }
        return "";
    }

    private static (string Vid, string Pid, string Vendor, string Product) ParseHardwareIds(string pnpDeviceId)
    {
        string vid = "N/A", pid = "N/A", vendor = "Generic", product = "Storage";

        var vidIdx = pnpDeviceId.IndexOf("VID_", StringComparison.OrdinalIgnoreCase);
        if (vidIdx >= 0 && pnpDeviceId.Length >= vidIdx + 8)
            vid = pnpDeviceId.Substring(vidIdx + 4, 4);

        var pidIdx = pnpDeviceId.IndexOf("PID_", StringComparison.OrdinalIgnoreCase);
        if (pidIdx >= 0 && pnpDeviceId.Length >= pidIdx + 8)
            pid = pnpDeviceId.Substring(pidIdx + 4, 4);

        var venIdx = pnpDeviceId.IndexOf("VEN_", StringComparison.OrdinalIgnoreCase);
        if (venIdx >= 0)
        {
            var end = pnpDeviceId.IndexOf('&', venIdx);
            vendor = end > venIdx ? pnpDeviceId.Substring(venIdx + 4, end - venIdx - 4) : "Disk";
        }

        var prodIdx = pnpDeviceId.IndexOf("PROD_", StringComparison.OrdinalIgnoreCase);
        if (prodIdx >= 0)
        {
            var end = pnpDeviceId.IndexOf('&', prodIdx);
            product = end > prodIdx ? pnpDeviceId.Substring(prodIdx + 5, end - prodIdx - 5) : "Drive";
        }

        return (vid, pid, vendor, product);
    }
}

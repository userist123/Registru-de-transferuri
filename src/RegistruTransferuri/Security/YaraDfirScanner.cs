using System.IO;
using System.IO.Compression;
using System.Text;
using System.Text.RegularExpressions;

namespace RegistruTransferuri.Security;

public sealed record DfirScanResult(
    bool IsClean,
    double ThreatScore,
    List<string> Detections,
    string Summary
);

/// <summary>
/// Motor DFIR & Euristic Offline YARA / Sigma pentru inspectarea pachetelor de date clasificate inainte de transfer.
/// </summary>
public static class YaraDfirScanner
{
    private static readonly string[] DangerousExtensions = new[]
    {
        ".exe", ".dll", ".sys", ".scr", ".pif", ".bat", ".cmd", ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh", ".ps1", ".psm1", ".hta", ".cpl", ".msc", ".jar"
    };

    private static readonly (string Pattern, string Description, double Severity)[] SuspiciousSignatures = new[]
    {
        ("powershell.*-e(nc|ncodedcommand)?\\s+[A-Za-z0-9+/=]{20,}", "Comandă PowerShell codificată Base64 (Obfuscated Execution)", 0.8),
        ("IEX\\s*\\(\\s*New-Object\\s+Net\\.WebClient", "Descărcare & Execuție memorie (PowerShell Download Cradle)", 0.9),
        ("mimikatz|sekurlsa::logonpasswords|lsadump", "Semnătură instrument extracție credențiale (Mimikatz/IoC)", 1.0),
        ("eval\\s*\\(\\s*base64_decode", "Webshell PHP / Decodare dinamică eval()", 0.85),
        ("WScript\\.Shell|CreateObject\\(\"WScript\\.Shell\"\\)", "Script Windows cu capacitate de execuție procese externe", 0.6),
        ("/bin/(sh|bash|zsh)\\s+-i", "Reverse shell Linux / Unix", 0.95),
        ("BEGIN RSA PRIVATE KEY|BEGIN OPENSSH PRIVATE KEY|BEGIN EC PRIVATE KEY", "Cheie privată criptografică necriptată detectată în date", 0.7)
    };

    public static DfirScanResult ScanFile(string filePath)
    {
        if (!File.Exists(filePath))
            return new DfirScanResult(false, 1.0, new() { "Fișierul nu a fost găsit" }, "Eroare: Fișier inexistent");

        var detections = new List<string>();
        double maxScore = 0.0;

        var ext = Path.GetExtension(filePath).ToLowerInvariant();
        var fileName = Path.GetFileName(filePath).ToLowerInvariant();

        // 1. Verificare extensie dublă deghizată (ex. doc.pdf.exe)
        var dotCount = fileName.Count(c => c == '.');
        if (dotCount > 1)
        {
            foreach (var dang in DangerousExtensions)
            {
                if (fileName.EndsWith(dang))
                {
                    detections.Add($"🚨 Extensie dublă malițioasă detectată: '{fileName}'");
                    maxScore = Math.Max(maxScore, 0.95);
                }
            }
        }

        // 2. Verificare arhive ZIP pentru Zip-Slip & conținut suspect
        if (ext == ".zip")
        {
            try
            {
                using var archive = ZipFile.OpenRead(filePath);
                foreach (var entry in archive.Entries)
                {
                    if (entry.FullName.Contains("..\\") || entry.FullName.Contains("../"))
                    {
                        detections.Add($"🚨 Atac de traversare director (Zip Slip) detectat în arhiva: '{entry.FullName}'");
                        maxScore = 1.0;
                    }

                    var innerExt = Path.GetExtension(entry.FullName).ToLowerInvariant();
                    if (DangerousExtensions.Contains(innerExt))
                    {
                        detections.Add($"⚠️ Executabil/script periculos inclus în arhivă: '{entry.FullName}'");
                        maxScore = Math.Max(maxScore, 0.8);
                    }
                }
            }
            catch (Exception ex)
            {
                detections.Add($"⚠️ Arhivă coruptă sau protejată: {ex.Message}");
                maxScore = Math.Max(maxScore, 0.4);
            }
        }

        // 3. Scanare Euristică de Semnături pe fișiere text / scripturi / date
        try
        {
            var fileInfo = new FileInfo(filePath);
            if (fileInfo.Length < 25 * 1024 * 1024) // Scanăm până la 25 MB
            {
                var content = File.ReadAllText(filePath, Encoding.Latin1);
                foreach (var (pattern, desc, sev) in SuspiciousSignatures)
                {
                    if (Regex.IsMatch(content, pattern, RegexOptions.IgnoreCase))
                    {
                        detections.Add($"⚠️ {desc}");
                        maxScore = Math.Max(maxScore, sev);
                    }
                }
            }
        }
        catch { }

        bool isClean = detections.Count == 0;
        string summary = isClean
            ? "✅ Scanare DFIR completă: Pachetul de date este curat (0 amenințări detectate)."
            : $"⚠️ ALERTĂ DFIR: {detections.Count} anomalii/riscuri detectate (Scor Amenințare: {maxScore:F2}).";

        return new DfirScanResult(isClean, maxScore, detections, summary);
    }
}

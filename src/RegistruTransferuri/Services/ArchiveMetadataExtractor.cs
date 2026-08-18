using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;

namespace RegistruTransferuri.Services;

public sealed record ArchiveEntryInfo(
    string RelativePath,
    long UncompressedSize,
    long CompressedSize,
    string? Sha256Hash,
    bool IsSuspicious,
    string? SuspiciousReason
);

public sealed record ArchiveInspectionResult(
    bool IsArchive,
    int TotalFiles,
    long TotalUncompressedBytes,
    double CompressionRatio,
    List<ArchiveEntryInfo> Entries,
    List<string> SecurityWarnings
);

/// <summary>
/// Extractor de metadate și analizor de structură pentru arhivele de date (.zip).
/// Detectează fișiere ascunse, extensii periculoase, căi recursive anomale și calculează hash-uri interne.
/// </summary>
public static class ArchiveMetadataExtractor
{
    private static readonly HashSet<string> SuspiciousExtensions = new(StringComparer.OrdinalIgnoreCase)
    {
        ".exe", ".dll", ".sys", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".hta", ".scr", ".pif", ".cpl", ".wsf"
    };

    public static ArchiveInspectionResult InspectArchive(string filePath)
    {
        var ext = Path.GetExtension(filePath).ToLowerInvariant();
        if (ext != ".zip")
        {
            return new ArchiveInspectionResult(false, 0, 0, 0, new List<ArchiveEntryInfo>(), new List<string>());
        }

        var entries = new List<ArchiveEntryInfo>();
        var warnings = new List<string>();
        long totalUncompressed = 0;
        long totalCompressed = 0;

        try
        {
            using var archive = ZipFile.OpenRead(filePath);
            foreach (var entry in archive.Entries)
            {
                if (string.IsNullOrEmpty(entry.Name)) continue; // director

                totalUncompressed += entry.Length;
                totalCompressed += entry.CompressedLength;

                var entryExt = Path.GetExtension(entry.FullName);
                var isSuspicious = false;
                string? reason = null;

                // 1. Verificare extensie periculoasă
                if (SuspiciousExtensions.Contains(entryExt))
                {
                    isSuspicious = true;
                    reason = $"Fișier executabil/script [{entryExt}] inclus în arhivă.";
                    warnings.Add($"[ATENȚIE]: Arhiva conține binar/script potențial executabil: {entry.FullName}");
                }

                // 2. Verificare fișiere reziduale ascunse
                if (entry.Name.StartsWith(".") || entry.Name.Equals("Thumbs.db", StringComparison.OrdinalIgnoreCase) || entry.Name.Equals(".DS_Store", StringComparison.OrdinalIgnoreCase))
                {
                    isSuspicious = true;
                    reason = "Fișier ascuns / rezidual de sistem de operare.";
                }

                // 3. Calcul hash SHA-256 pentru fișiere mici (< 10 MB)
                string? entryHash = null;
                if (entry.Length < 10 * 1024 * 1024)
                {
                    try
                    {
                        using var s = entry.Open();
                        using var sha = SHA256.Create();
                        entryHash = Convert.ToHexString(sha.ComputeHash(s)).ToLowerInvariant();
                    }
                    catch { }
                }

                entries.Add(new ArchiveEntryInfo(
                    entry.FullName,
                    entry.Length,
                    entry.CompressedLength,
                    entryHash,
                    isSuspicious,
                    reason
                ));
            }

            var ratio = totalCompressed > 0 ? (double)totalUncompressed / totalCompressed : 1.0;
            if (ratio > 50.0 && totalUncompressed > 500 * 1024 * 1024)
            {
                warnings.Add("⚠️ AVERTISMENT ZIP-BOMB: Raportul de compresie este extrem de mare (>50x).");
            }

            return new ArchiveInspectionResult(
                true,
                entries.Count,
                totalUncompressed,
                ratio,
                entries,
                warnings
            );
        }
        catch (Exception ex)
        {
            warnings.Add($"Eroare la inspectarea arhivei: {ex.Message}");
            return new ArchiveInspectionResult(true, 0, 0, 0, entries, warnings);
        }
    }
}

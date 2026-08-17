using System.IO;

namespace RegistruTransferuri.Security;

public enum PayloadFileType
{
    Unknown,
    ZipArchive,
    PdfDocument,
    OfficeDocument,
    ImageMedia,
    TextData,
    ExecutableBlocked // MZ, PE, ELF, Mach-O
}

/// <summary>
/// Modul DLP & Inspecție Structurală Magic Bytes (Antet Binar) pentru Prevenirea Atacurilor cu Payload-uri Deghizate.
/// </summary>
public static class PayloadDlpInspector
{
    private static readonly byte[] MagicMz = new byte[] { 0x4D, 0x5A }; // "MZ" Windows Executable
    private static readonly byte[] MagicElf = new byte[] { 0x7F, 0x45, 0x4C, 0x46 }; // ELF Linux Executable
    private static readonly byte[] MagicPdf = new byte[] { 0x25, 0x50, 0x44, 0x46 }; // "%PDF"
    private static readonly byte[] MagicZip = new byte[] { 0x50, 0x4B, 0x03, 0x04 }; // "PK.." Zip Archive
    private static readonly byte[] MagicPng = new byte[] { 0x89, 0x50, 0x4E, 0x47 }; // PNG Image
    private static readonly byte[] MagicJpg = new byte[] { 0xFF, 0xD8, 0xFF }; // JPEG Image

    public sealed record InspectionResult(
        bool IsSafe,
        PayloadFileType DetectedType,
        string DetectedMime,
        string Details
    );

    public static InspectionResult InspectFile(string filePath)
    {
        if (!File.Exists(filePath))
            return new InspectionResult(false, PayloadFileType.Unknown, "unknown", "Fișierul nu există.");

        try
        {
            using var fs = new FileStream(filePath, FileMode.Open, FileAccess.Read, FileShare.Read);
            var header = new byte[32];
            var bytesRead = fs.Read(header, 0, header.Length);

            if (bytesRead < 4)
                return new InspectionResult(false, PayloadFileType.Unknown, "unknown", "Dimensiune insuficientă pentru validare antet binar.");

            // 1. Verificare Executabile Malițioase Deghizate (MZ / PE)
            if (header[0] == MagicMz[0] && header[1] == MagicMz[1])
            {
                return new InspectionResult(
                    false,
                    PayloadFileType.ExecutableBlocked,
                    "application/x-dosexec",
                    "⚠️ BLOCAT DE SECURITATE: Fișierul conține antet de executabil binar Windows (MZ/PE) și este strict interzis pentru transfer!"
                );
            }

            // 2. Verificare ELF Linux
            if (bytesRead >= 4 && header[0] == MagicElf[0] && header[1] == MagicElf[1] && header[2] == MagicElf[2] && header[3] == MagicElf[3])
            {
                return new InspectionResult(
                    false,
                    PayloadFileType.ExecutableBlocked,
                    "application/x-executable",
                    "⚠️ BLOCAT DE SECURITATE: Fișierul conține antet de binar executabil Linux ELF!"
                );
            }

            // 3. Verificare Arhivă ZIP / DOCX / XLSX
            if (bytesRead >= 4 && header[0] == MagicZip[0] && header[1] == MagicZip[1] && header[2] == MagicZip[2] && header[3] == MagicZip[3])
            {
                return new InspectionResult(
                    true,
                    PayloadFileType.ZipArchive,
                    "application/zip",
                    "✅ Antet valid: Arhivă compusă securizată / Pachet container."
                );
            }

            // 4. Verificare PDF
            if (bytesRead >= 4 && header[0] == MagicPdf[0] && header[1] == MagicPdf[1] && header[2] == MagicPdf[2] && header[3] == MagicPdf[3])
            {
                return new InspectionResult(
                    true,
                    PayloadFileType.PdfDocument,
                    "application/pdf",
                    "✅ Antet valid: Document oficial format PDF."
                );
            }

            // 5. Verificare Imagini (PNG / JPG)
            if (bytesRead >= 4 && header[0] == MagicPng[0] && header[1] == MagicPng[1] && header[2] == MagicPng[2] && header[3] == MagicPng[3])
            {
                return new InspectionResult(
                    true,
                    PayloadFileType.ImageMedia,
                    "image/png",
                    "✅ Antet valid: Fișier imagine raster PNG."
                );
            }

            if (bytesRead >= 3 && header[0] == MagicJpg[0] && header[1] == MagicJpg[1] && header[2] == MagicJpg[2])
            {
                return new InspectionResult(
                    true,
                    PayloadFileType.ImageMedia,
                    "image/jpeg",
                    "✅ Antet valid: Fișier imagine raster JPEG."
                );
            }

            return new InspectionResult(
                true,
                PayloadFileType.TextData,
                "application/octet-stream",
                "ℹ️ Fișier de date generale (structură binară verificată fără semnături executabile)."
            );
        }
        catch (Exception ex)
        {
            return new InspectionResult(false, PayloadFileType.Unknown, "error", $"Eroare la inspecția structurală: {ex.Message}");
        }
    }
}

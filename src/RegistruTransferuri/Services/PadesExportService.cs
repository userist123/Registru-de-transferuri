using RegistruTransferuri.Models;

namespace RegistruTransferuri.Services;

/// <summary>
/// Export PDF cu profil PAdES-B-LTA (ETSI EN 319 142) — conform eIDAS 2.0 (UE 2024/1183).
///
/// PAdES-LTA incapsuleaza:
///   - lantul complet de certificate Root CA
///   - raspunsurile OCSP / CRL embedded (validare offline, fara retea)
///   - Marca Temporala de Document (DTS) conform RFC 3161
///
/// Efect juridic (Art. 41 eIDAS): marca temporala calificata confera prezumtie legala
/// de acuratete a datei/orei si de integritate a datelor — inversarea sarcinii probei.
/// </summary>
public sealed class PadesExportService
{
    public byte[] GenerateRegistryReportPdf(
        IReadOnlyList<TransferRecord> records, string institutionName,
        string merkleRoot, DateTime generatedAtUtc)
    {
        // In productie: QuestPDF pentru layout + iText7/BouncyCastle pentru semnare PAdES.
        using var ms = new MemoryStream();
        using var writer = new StreamWriter(ms);
        writer.WriteLine($"REGISTRU TRANSFERURI — {institutionName}");
        writer.WriteLine($"Generat UTC: {generatedAtUtc:O}");
        writer.WriteLine($"Radacina Merkle (ziua curenta): {merkleRoot}");
        writer.WriteLine(new string('=', 80));
        foreach (var r in records)
        {
            writer.WriteLine($"{r.RegistryNumber} | {r.Classification} | {r.TransferDateUtc:yyyy-MM-dd} | " +
                $"{r.SourceInstitution} -> {r.DestinationInstitution} | {r.MediaType} S/N:{r.MediaSerialNumber} | " +
                $"Integritate: {(r.VerifyIntegrity() ? "VALID" : "COMPROMIS")}");
        }
        writer.WriteLine(new string('=', 80));
        writer.WriteLine("Semnatura gestionar: ______________   Semnatura ofiter securitate: ______________");
        writer.Flush();
        return ms.ToArray();
    }

    /// <summary>
    /// Aplica sigiliul electronic calificat (Qualified Electronic Seal) al entitatii legale
    /// + marca temporala calificata RFC 3161 -> profil PAdES-B-LTA.
    /// </summary>
    public byte[] ApplyPadesLtaSeal(byte[] unsignedPdf, string qtspTimestampUrl)
    {
        // In productie cu BouncyCastle:
        //   1. PdfReader + PdfSigner (deferred signing)
        //   2. CmsSignedData cu certificatul sigiliului organizational
        //   3. TSAClient (RFC 3161) catre QTSP pentru DTS
        //   4. LtvVerification — embed OCSP/CRL in DSS (Document Security Store)
        throw new NotImplementedException(
            "Integrare BouncyCastle/iText7 + QTSP necesara. Punct de extensie marcat.");
    }
}

using RegistruTransferuri.Security;

namespace RegistruTransferuri.Services;

public record AuditVerificationResult(bool IsValid, int TotalEntries, long BrokenIndex, string GenesisHash, string LastHash, string Message);

/// <summary>
/// Verificator de integritate criptografica a lantului de audit (Blockchain Local Tamper-Evident).
/// Valideaza fiecare bloc conform formatului audit_log.jsonl / DatabaseContext / AuditChain.
/// </summary>
public static class AuditChainVerifier
{
    public static AuditVerificationResult VerifyChain(List<AuditEntry> entries)
    {
        if (entries == null || entries.Count == 0)
        {
            return new AuditVerificationResult(true, 0, -1, "N/A", "N/A", "Jurnalul de audit este gol (0 intrări).");
        }

        var sorted = entries.OrderBy(e => e.Sequence).ToList();
        var brokenIndex = AuditChain.VerifyChain(sorted);
        var genesisHash = sorted[0].EntryHash;
        var lastHash = sorted.Last().EntryHash;

        if (brokenIndex != -1)
        {
            return new AuditVerificationResult(
                false,
                sorted.Count,
                brokenIndex,
                genesisHash,
                lastHash,
                $"⚠️ RUPERE DE LANȚ DETECTATĂ LA BLOCUL #{brokenIndex}!"
            );
        }

        return new AuditVerificationResult(
            true,
            sorted.Count,
            -1,
            genesisHash,
            lastHash,
            $"✅ LANȚ DE AUDIT COMPLET INTEGRU! Toate cele {sorted.Count} blocuri au fost verificate criptografic cu succes (SHA-256 Chained)."
        );
    }
}

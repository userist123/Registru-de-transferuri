using System.Security.Cryptography;
using System.Text;

namespace RegistruTransferuri.Security;

/// <summary>
/// Lant criptografic de audit (hash chain) — tamper-evident conform NIST SP 800-92.
/// H(n) = SHA-256( H(n-1) || seq || timestamp || action || operator || details )
/// Orice modificare/stergere/inserare invalideaza toate hash-urile ulterioare.
/// </summary>
public static class AuditChain
{
    public const string GenesisHash = "0000000000000000000000000000000000000000000000000000000000000000";

    public static string ComputeEntryHash(
        string previousHash, long sequence, DateTime timestampUtc,
        string action, string operatorUsername, string details)
    {
        var canonical = string.Join("\u001f", new[]
        {
            previousHash,
            sequence.ToString(),
            timestampUtc.ToString("O"),
            action,
            operatorUsername,
            details
        });
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(canonical)));
    }

    /// <summary>
    /// Verifica intregul lant. Returneaza secventa primei intrari compromise sau -1 daca e valid.
    /// Detecteaza: modificare (hash mismatch), stergere (gap in secventa), inserare (ruptura de link).
    /// </summary>
    public static long VerifyChain(IReadOnlyList<AuditEntry> entries)
    {
        var expectedPrev = GenesisHash;
        long expectedSeq = 1;
        foreach (var e in entries)
        {
            if (e.Sequence != expectedSeq) return e.Sequence;
            var recomputed = ComputeEntryHash(e.PreviousHash, e.Sequence, e.TimestampUtc,
                e.Action, e.OperatorUsername, e.Details);
            if (!string.Equals(recomputed, e.EntryHash, StringComparison.OrdinalIgnoreCase))
                return e.Sequence;
            if (!string.Equals(e.PreviousHash, expectedPrev, StringComparison.OrdinalIgnoreCase))
                return e.Sequence;
            expectedPrev = e.EntryHash;
            expectedSeq++;
        }
        return -1;
    }
}

public sealed record AuditEntry(
    long Sequence, DateTime TimestampUtc, string Action,
    string OperatorUsername, string Details, string PreviousHash, string EntryHash);

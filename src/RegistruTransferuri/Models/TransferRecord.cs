using System.Security.Cryptography;
using System.Text;

namespace RegistruTransferuri.Models;

/// <summary>Inregistrare de transfer — toate campurile canonice intra in hash-ul de integritate.</summary>
public sealed class TransferRecord
{
    public long Id { get; set; }
    public string RegistryNumber { get; set; } = "";
    public ClassificationLevel Classification { get; set; }
    public DateTime TransferDateUtc { get; set; }
    public string SourceInstitution { get; set; } = "";
    public string DestinationInstitution { get; set; } = "";
    public string SourcePerson { get; set; } = "";
    public string DestinationPerson { get; set; } = "";
    public string MediaType { get; set; } = "";
    public string MediaSerialNumber { get; set; } = "";
    public string MediaInventoryCode { get; set; } = "";
    public string ContentDescription { get; set; } = "";
    public string OperatorUsername { get; set; } = "";
    public bool Signed { get; set; }
    public DateTime? SignedAtUtc { get; set; }
    public string? SignedBy { get; set; }
    public bool Cancelled { get; set; }
    public string? CancellationReason { get; set; }
    public string IntegrityHash { get; set; } = "";

    /// <summary>
    /// Hash de integritate complet — remediaza vulnerabilitatea v2.0 unde hash-ul
    /// acoperea doar nr + institutia sursa. Acum include toate campurile de business.
    /// </summary>
    public string ComputeIntegrityHash()
    {
        var canonical = string.Join("\u001f", new[]
        {
            RegistryNumber,
            ((int)Classification).ToString(),
            TransferDateUtc.ToString("O"),
            SourceInstitution.Trim(),
            DestinationInstitution.Trim(),
            SourcePerson.Trim(),
            DestinationPerson.Trim(),
            MediaType.Trim(),
            MediaSerialNumber.Trim(),
            MediaInventoryCode.Trim(),
            ContentDescription.Trim(),
            OperatorUsername.Trim()
        });
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(canonical));
        return Convert.ToHexString(bytes);
    }

    public bool VerifyIntegrity() =>
        string.Equals(IntegrityHash, ComputeIntegrityHash(), StringComparison.OrdinalIgnoreCase);
}

namespace RegistruTransferuri.Models;

public enum MediaStatus
{
    AutorizatRw = 0,
    AutorizatRo = 1,
    InAsteptare = 2,
    Blocat = 3,
    Sanitizat = 4,
    Distrus = 5
}

/// <summary>
/// Model de evidenta pentru suporturile de memorie (Endpoint Protector Model & HG 585/2002).
/// Telemetria hardware fizica (VID, PID, S/N Firmware) este strict READ-ONLY / IMUABILA (P16).
/// Utilizatorul poate modifica FriendlyName si metadatele administrative (P17).
/// </summary>
public sealed class MediaAsset
{
    public int Id { get; set; }
    public string SerialNumber { get; set; } = string.Empty; // S/N Hardware (Imuabil 🔒)
    public string InventoryCode { get; set; } = string.Empty; // Nr. Inregistrare Mediu (ex: 0-1045/2026)
    public string FriendlyName { get; set; } = string.Empty;  // Denumire Personalizata Volum (ex: Stick Transfer Operativ)
    public string MediaType { get; set; } = "Stick USB Flash";
    public string VendorId { get; set; } = string.Empty;     // VID
    public string ProductId { get; set; } = string.Empty;    // PID
    public string Manufacturer { get; set; } = string.Empty;
    public string Model { get; set; } = string.Empty;
    public long CapacityBytes { get; set; }
    public double CapacityGb => Math.Round((double)CapacityBytes / (1024 * 1024 * 1024), 2);
    public ClassificationLevel MaxClassification { get; set; } = ClassificationLevel.Secret;
    public MediaStatus Status { get; set; } = MediaStatus.AutorizatRw;
    public string EncryptionStatus { get; set; } = "BitLocker To Go (AES-256)";
    public string CustodianName { get; set; } = string.Empty;
    public string CustodianUnit { get; set; } = "MApN / Structura Securitate";
    public string Notes { get; set; } = string.Empty;
    public DateTime DateEnrolledUtc { get; set; } = DateTime.UtcNow;

    // NIST SP 800-88r2 Sanitization Info
    public int? SanitizationMethod { get; set; } // 1: Clear, 2: Purge, 3: Destroy
    public string? DestructionCertNumber { get; set; }
    public DateTime? SanitizedAtUtc { get; set; }
    public string? SanitizedBy { get; set; }
    public string? VerifiedByWitness { get; set; }
}

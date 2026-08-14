namespace RegistruTransferuri.Models;

/// <summary>Suport de stocare inventariat — ciclu de viata complet pana la casare.</summary>
public sealed class MediaAsset
{
    public long Id { get; set; }
    public string SerialNumber { get; set; } = "";
    public string InventoryCode { get; set; } = "";
    public string MediaType { get; set; } = "";
    public string VendorId { get; set; } = "";
    public string ProductId { get; set; } = "";
    public long CapacityBytes { get; set; }
    public ClassificationLevel MaxClassificationHandled { get; set; }
    public string PhysicalLocation { get; set; } = "";
    public MediaLifecycleStatus Status { get; set; } = MediaLifecycleStatus.InService;
    public SanitizationMethod? SanitizationApplied { get; set; }
    public string? DestructionCertificateNumber { get; set; }
    public DateTime? SanitizedAtUtc { get; set; }
    public string? SanitizedBy { get; set; }
    public string? VerifiedBy { get; set; }
}

public enum MediaLifecycleStatus
{
    InService = 0,
    PendingSanitization = 1,
    Sanitized = 2,
    Destroyed = 3
}

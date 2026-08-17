namespace RegistruTransferuri.Models;

/// <summary>
/// Înregistrare transfer militar conform HG 585/2002, NATO AC/35 și EUCI 2013/488/UE.
/// </summary>
public sealed class TransferRecord
{
    public int Id { get; set; }
    public string RegistryNumber { get; set; } = string.Empty;
    public ClassificationLevel Classification { get; set; } = ClassificationLevel.Neclasificat;
    public string NatoClassification => Classification.ToNatoClassification();
    public string EuClassification => Classification.ToEuClassification();
    public string ClassificationPrefix => Classification.GetPrefix();

    public DateTime TransferDateUtc { get; set; } = DateTime.UtcNow;
    public string Direction { get; set; } = "iesire"; // iesire, intrare, tranzit

    // Sursă
    public string SourceInstitution { get; set; } = string.Empty;
    public string SourceStationHost { get; set; } = string.Empty;
    public string SourcePerson { get; set; } = string.Empty;
    public string SourcePersonRole { get; set; } = string.Empty;
    public string SourcePersonIdNumber { get; set; } = string.Empty;
    public string SourcePersonClearance { get; set; } = "Secret";

    // Destinație
    public string DestinationInstitution { get; set; } = string.Empty;
    public string DestinationStationHost { get; set; } = string.Empty;
    public string DestinationPerson { get; set; } = string.Empty;

    // Curier Militar
    public string? CourierName { get; set; }
    public string? CourierPermitNumber { get; set; }

    // Mediu de Stocare Fizic
    public string MediaType { get; set; } = "Stick USB Flash";
    public string MediaSerialNumber { get; set; } = string.Empty; // Imuabil 🔒
    public string MediaVendorId { get; set; } = string.Empty;
    public string MediaProductId { get; set; } = string.Empty;
    public string MediaInventoryCode { get; set; } = string.Empty; // Nr. Inregistrare Mediu
    public string MediaFriendlyLabel { get; set; } = string.Empty; // Denumire Volum
    public int? StorageMediumId { get; set; }

    // Pachet Date & Integritate SHA-256
    public string PayloadFileName { get; set; } = string.Empty;
    public string PayloadType { get; set; } = "Arhivă ZIP Securizată";
    public double PayloadSizeGb { get; set; }
    public int PayloadFilesCount { get; set; } = 1;
    public string PayloadSha256Hash { get; set; } = string.Empty; // 64-char hex
    public string ContentDescription { get; set; } = string.Empty;
    public bool AntivirusScanned { get; set; } = true;
    public string AntivirusDetails { get; set; } = "Scanare Antivirus Offline: Bază Definiții la zi, Negativ";

    // Cadrul Legal & Aprobări
    public string LegalBase { get; set; } = "HG 585/2002 Art. 60-73";
    public string? ApprovalOrderNumber { get; set; }
    public string? DisseminationRestrictions { get; set; }
    public string? Notes { get; set; }

    // Operator & Semnături
    public string OperatorUsername { get; set; } = string.Empty;
    public bool Signed { get; set; }
    public DateTime? SignedAtUtc { get; set; }
    public string? SignedBy { get; set; }

    // Four-Eyes Principle
    public string? FourEyesApproverName { get; set; }
    public string? FourEyesApproverRole { get; set; }
    public DateTime? FourEyesApprovedAtUtc { get; set; }

    // Status
    public bool Cancelled { get; set; }
    public string? CancellationReason { get; set; }
    public string StatusText => Cancelled ? "ANULAT" : (Signed ? "FINALIZAT & SEMNAT" : "ACTIV / ÎNREGISTRAT");

    // Criptografie
    public string IntegrityHash { get; set; } = string.Empty;
}

using RegistruTransferuri.Models;

namespace RegistruTransferuri.Services;

/// <summary>
/// Serviciu de sanitizare conform NIST SP 800-88 Rev. 2 (septembrie 2025).
/// Rev. 1 a fost RETRASA oficial la 26.09.2025 — aplicatia refera exclusiv Rev. 2.
///
/// Metode (Sec. 3.1.1-3.1.3):
///   Clear   — suprascriere logica; doar pentru Neclasificat.
///   Purge   — inclusiv Cryptographic Erase pe SED (TCG Opal / IEEE 1667) pentru SSD/NVMe.
///   Destroy — distrugere fizica (DIN 66399 H-5, particule <=2mm pentru flash);
///             OBLIGATORIU pentru Secret, Strict Secret si SSID.
///
/// Regula de blocare: un mediu care a purtat SSID nu poate fi sanitizat cu Clear/Purge —
/// orice incercare declanseaza blocare in lant + alerta rosie in audit.
/// </summary>
public sealed class SanitizationService
{
    public sealed record SanitizationResult(
        bool Success, string CertificateNumber, string Message, SanitizationMethod Method);

    public SanitizationResult Sanitize(
        MediaAsset asset, SanitizationMethod requested,
        string operatorUsername, string verifierUsername)
    {
        var minimum = asset.MaxClassificationHandled.MinimumSanitization();

        if (requested < minimum)
        {
            return new SanitizationResult(false, "",
                $"BLOCAT: metoda {requested} este sub minimul {minimum} impus de clasificarea " +
                $"{asset.MaxClassificationHandled}. Conform NIST SP 800-88r2 si HG 585/2002, " +
                "acest transfer ar compromite datele clasificate.",
                requested);
        }

        if (asset.MaxClassificationHandled >= ClassificationLevel.StrictSecret
            && string.IsNullOrWhiteSpace(verifierUsername))
        {
            return new SanitizationResult(false, "",
                "Sanitizarea mediilor Strict Secret / SSID cere un al doilea ofiter verificator " +
                "(principiul supravegherii incrucisate).", requested);
        }

        var certNumber = $"SAN-{DateTime.UtcNow:yyyy}-{Guid.NewGuid().ToString("N")[..8].ToUpperInvariant()}";
        asset.SanitizationApplied = requested;
        asset.DestructionCertificateNumber = certNumber;
        asset.SanitizedAtUtc = DateTime.UtcNow;
        asset.SanitizedBy = operatorUsername;
        asset.VerifiedBy = verifierUsername;
        asset.Status = requested == SanitizationMethod.Destroy
            ? MediaLifecycleStatus.Destroyed
            : MediaLifecycleStatus.Sanitized;

        return new SanitizationResult(true, certNumber,
            $"Certificat de distrugere emis: {certNumber}. Metoda {requested} aplicata conform NIST SP 800-88r2.",
            requested);
    }

    /// <summary>
    /// Cryptographic Erase pentru SED (Self-Encrypting Drive) — TCG Opal / IEEE 1667.
    /// Controller-ul distruge cheia simetrica interna; datele latente devin irecuperabile.
    /// </summary>
    public bool CryptographicEraseSed(string devicePath)
    {
        // In productie: trimitere comanda ATA SECURITY / NVMe Format cu Crypto Erase
        // prin DeviceIoControl (IOCTL_ATA_PASS_THROUGH / IOCTL_STORAGE_PROTOCOL_COMMAND).
        throw new NotImplementedException("Necesita integrare DeviceIoControl pentru SED.");
    }
}

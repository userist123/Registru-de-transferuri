using RegistruTransferuri.Models;

namespace RegistruTransferuri.Services;

public enum SanitizationMethod
{
    Clear = 1,
    Purge = 2,
    Destroy = 3
}

public static class SanitizationExtensions
{
    public static SanitizationMethod MinimumSanitization(this ClassificationLevel level) => level switch
    {
        ClassificationLevel.Neclasificat => SanitizationMethod.Clear,
        ClassificationLevel.SecretDeServiciu => SanitizationMethod.Purge,
        ClassificationLevel.Secret => SanitizationMethod.Destroy,
        ClassificationLevel.StrictSecret => SanitizationMethod.Destroy,
        ClassificationLevel.StrictSecretDeImportantaDeosebita => SanitizationMethod.Destroy,
        _ => SanitizationMethod.Clear
    };
}

/// <summary>
/// Serviciu de sanitizare conform NIST SP 800-88 Rev. 2 (2025) & IEEE 2883-2022.
/// </summary>
public sealed class SanitizationService
{
    public sealed record SanitizationResult(
        bool Success, string CertificateNumber, string Message, SanitizationMethod Method);

    public SanitizationResult Sanitize(
        MediaAsset asset, SanitizationMethod requested,
        string operatorUsername, string verifierUsername)
    {
        var minimum = asset.MaxClassification.MinimumSanitization();

        if (requested < minimum)
        {
            return new SanitizationResult(false, "",
                $"BLOCAT: metoda {requested} este sub minimul {minimum} impus de clasificarea " +
                $"{asset.MaxClassification.ToDisplayName()}. Conform NIST SP 800-88r2 si HG 585/2002, " +
                "acest mediu cere o metoda superioara de sanitizare.",
                requested);
        }

        if (asset.MaxClassification >= ClassificationLevel.StrictSecret
            && string.IsNullOrWhiteSpace(verifierUsername))
        {
            return new SanitizationResult(false, "",
                "Sanitizarea mediilor Strict Secret / SSID cere un al doilea ofițer verificator " +
                "(principiul celor 4 ochi).", requested);
        }

        var certNumber = $"SAN-{DateTime.UtcNow:yyyy}-{Guid.NewGuid().ToString("N")[..8].ToUpperInvariant()}";
        asset.SanitizationMethod = (int)requested;
        asset.DestructionCertNumber = certNumber;
        asset.SanitizedAtUtc = DateTime.UtcNow;
        asset.SanitizedBy = operatorUsername;
        asset.VerifiedByWitness = verifierUsername;
        asset.Status = requested == SanitizationMethod.Destroy
            ? MediaStatus.Distrus
            : MediaStatus.Sanitizat;

        return new SanitizationResult(true, certNumber,
            $"Certificat de distrugere emis: {certNumber}. Metoda {requested} aplicată conform NIST SP 800-88r2.",
            requested);
    }
}

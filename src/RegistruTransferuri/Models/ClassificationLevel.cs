namespace RegistruTransferuri.Models;

/// <summary>
/// Niveluri de clasificare conform HG 585/2002 + echivalenta EUCI (Decizia Consiliului 2013/488/UE).
/// Prefixul de inregistrare este impus de Art. 41 HG 585/2002.
/// </summary>
public enum ClassificationLevel
{
    /// <summary>Neclasificat — prefix NC, echivalent EU: Unclassified</summary>
    Neclasificat = 0,
    /// <summary>Secret de Serviciu — prefix S, echivalent EU: RESTREINT UE / EU RESTRICTED</summary>
    SecretDeServiciu = 1,
    /// <summary>Secret — prefix 0, echivalent EU: CONFIDENTIEL UE / EU CONFIDENTIAL</summary>
    Secret = 2,
    /// <summary>Strict Secret — prefix 00, echivalent EU: SECRET UE / EU SECRET</summary>
    StrictSecret = 3,
    /// <summary>Strict Secret de Importanta Deosebita — prefix 000, echivalent EU: TRES SECRET UE / EU TOP SECRET</summary>
    StrictSecretImportantaDeosebita = 4
}

public static class ClassificationLevelExtensions
{
    /// <summary>Prefix obligatoriu conform Art. 41 HG 585/2002.</summary>
    public static string RegistryPrefix(this ClassificationLevel level) => level switch
    {
        ClassificationLevel.StrictSecretImportantaDeosebita => "000",
        ClassificationLevel.StrictSecret => "00",
        ClassificationLevel.Secret => "0",
        ClassificationLevel.SecretDeServiciu => "S",
        ClassificationLevel.Neclasificat => "NC",
        _ => throw new ArgumentOutOfRangeException(nameof(level))
    };

    /// <summary>Echivalent EUCI conform Deciziei Consiliului 2013/488/UE.</summary>
    public static string EuciEquivalent(this ClassificationLevel level) => level switch
    {
        ClassificationLevel.StrictSecretImportantaDeosebita => "TRES SECRET UE / EU TOP SECRET",
        ClassificationLevel.StrictSecret => "SECRET UE / EU SECRET",
        ClassificationLevel.Secret => "CONFIDENTIEL UE / EU CONFIDENTIAL",
        ClassificationLevel.SecretDeServiciu => "RESTREINT UE / EU RESTRICTED",
        ClassificationLevel.Neclasificat => "Unclassified",
        _ => throw new ArgumentOutOfRangeException(nameof(level))
    };

    /// <summary>
    /// Metoda minima de sanitizare conform NIST SP 800-88 Rev. 2 (sept. 2025).
    /// Rev. 1 a fost retrasa oficial la 26.09.2025 si inlocuita integral de Rev. 2.
    /// </summary>
    public static SanitizationMethod MinimumSanitization(this ClassificationLevel level) => level switch
    {
        ClassificationLevel.Neclasificat => SanitizationMethod.Clear,
        ClassificationLevel.SecretDeServiciu => SanitizationMethod.Purge,
        ClassificationLevel.Secret => SanitizationMethod.Destroy,
        ClassificationLevel.StrictSecret => SanitizationMethod.Destroy,
        ClassificationLevel.StrictSecretImportantaDeosebita => SanitizationMethod.Destroy,
        _ => SanitizationMethod.Destroy
    };
}

/// <summary>Metode de sanitizare conform NIST SP 800-88 Rev. 2 (2025), Sec. 3.1.1-3.1.3.</summary>
public enum SanitizationMethod
{
    /// <summary>Clear — suprascriere logica; doar pentru Neclasificat.</summary>
    Clear = 0,
    /// <summary>Purge — inclusiv Cryptographic Erase pe SED (TCG Opal / IEEE 1667).</summary>
    Purge = 1,
    /// <summary>Destroy — distrugere fizica (DIN 66399 H-5); obligatoriu pentru S/SS/SSID.</summary>
    Destroy = 2
}

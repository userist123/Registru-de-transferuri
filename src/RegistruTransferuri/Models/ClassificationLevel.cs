namespace RegistruTransferuri.Models;

/// <summary>
/// Niveluri de clasificare a secretizarii conform HG 585/2002, NATO AC/35-D/2000-REV8 si EUCI 2013/488/UE.
/// </summary>
public enum ClassificationLevel
{
    Neclasificat = 0,
    SecretDeServiciu = 1,
    Secret = 2,
    StrictSecret = 3,
    StrictSecretDeImportantaDeosebita = 4
}

public static class ClassificationExtensions
{
    public static string ToDisplayName(this ClassificationLevel level) => level switch
    {
        ClassificationLevel.Neclasificat => "Neclasificat",
        ClassificationLevel.SecretDeServiciu => "Secret de Serviciu",
        ClassificationLevel.Secret => "Secret",
        ClassificationLevel.StrictSecret => "Strict Secret",
        ClassificationLevel.StrictSecretDeImportantaDeosebita => "Strict Secret de Importanță Deosebită",
        _ => "Neclasificat"
    };

    public static string ToNatoClassification(this ClassificationLevel level) => level switch
    {
        ClassificationLevel.Neclasificat => "NATO UNCLASSIFIED",
        ClassificationLevel.SecretDeServiciu => "NATO RESTRICTED",
        ClassificationLevel.Secret => "NATO CONFIDENTIAL",
        ClassificationLevel.StrictSecret => "NATO SECRET",
        ClassificationLevel.StrictSecretDeImportantaDeosebita => "COSMIC TOP SECRET",
        _ => "NATO UNCLASSIFIED"
    };

    public static string ToEuClassification(this ClassificationLevel level) => level switch
    {
        ClassificationLevel.Neclasificat => "LIMITE / UNCLASSIFIED",
        ClassificationLevel.SecretDeServiciu => "RESTREINT UE / EU RESTRICTED",
        ClassificationLevel.Secret => "CONFIDENTIEL UE / EU CONFIDENTIAL",
        ClassificationLevel.StrictSecret => "SECRET UE / EU SECRET",
        ClassificationLevel.StrictSecretDeImportantaDeosebita => "TRÈS SECRET UE / EU TOP SECRET",
        _ => "LIMITE / UNCLASSIFIED"
    };

    public static string GetPrefix(this ClassificationLevel level) => level switch
    {
        ClassificationLevel.Neclasificat => "NC",
        ClassificationLevel.SecretDeServiciu => "S",
        ClassificationLevel.Secret => "0",
        ClassificationLevel.StrictSecret => "00",
        ClassificationLevel.StrictSecretDeImportantaDeosebita => "000",
        _ => "NC"
    };
}

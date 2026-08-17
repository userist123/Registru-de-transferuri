using RegistruTransferuri.Models;

namespace RegistruTransferuri.Services;

public enum SanitizationMethod
{
    Clear = 1,      // NIST 800-88r2 Logical Overwrite (pentru Neclasificat)
    Purge = 2,      // NIST 800-88r2 / IEEE 2883-2022 Cryptographic Erase SED (pentru Secret de Serviciu)
    Destroy = 3     // DIN 66399 H-5 / Dezintegrare Fizica (pentru Secret, SS, SSID)
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

    public static string ToStandardDescription(this SanitizationMethod method) => method switch
    {
        SanitizationMethod.Clear => "Clear — Suprascriere logică 1-pass (NIST SP 800-88r2 Sec. 3.1.1)",
        SanitizationMethod.Purge => "Purge — Cryptographic Erase IEEE 2883-2022 pe medii SED / TCG Opal cu distrugere MEK",
        SanitizationMethod.Destroy => "Destroy — Dezintegrare fizică DIN 66399 Clasa H-5 (particule <= 2mm)",
        _ => "Clear"
    };
}

/// <summary>
/// Serviciu de sanitizare conform NIST SP 800-88 Rev. 2 (2025) & IEEE 2883-2022 & HG 585/2002 Art. 65.
/// </summary>
public sealed class SanitizationService
{
    public sealed record SanitizationResult(
        bool Success, string CertificateNumber, string Message, SanitizationMethod Method, string DestructionPvHtml);

    public SanitizationResult Sanitize(
        MediaAsset asset, SanitizationMethod requested,
        string operatorUsername, string verifierUsername)
    {
        var minimum = asset.MaxClassification.MinimumSanitization();

        if (requested < minimum)
        {
            return new SanitizationResult(false, "",
                $"BLOCAT DE SECURITATE: Metoda aleasă [{requested}] este sub standardul minim [{minimum}] impus de nivelul " +
                $"{asset.MaxClassification.ToDisplayName()} conform NIST SP 800-88r2, IEEE 2883-2022 și HG 585/2002 Art. 65!",
                requested, string.Empty);
        }

        if (asset.MaxClassification >= ClassificationLevel.Secret
            && string.IsNullOrWhiteSpace(verifierUsername))
        {
            return new SanitizationResult(false, "",
                "Sanitizarea mediilor Secret / Strict Secret / SSID impune obligatoriu contrasemnarea de către un Ofițer de Securitate Verificator (Principiul celor 4 Ochi).",
                requested, string.Empty);
        }

        var certNumber = $"PV-DISTRUGERE-{DateTime.UtcNow:yyyy}-{Guid.NewGuid().ToString("N")[..8].ToUpperInvariant()}";
        asset.SanitizationMethod = (int)requested;
        asset.DestructionCertNumber = certNumber;
        asset.SanitizedAtUtc = DateTime.UtcNow;
        asset.SanitizedBy = operatorUsername;
        asset.VerifiedByWitness = verifierUsername;
        asset.Status = requested == SanitizationMethod.Destroy
            ? MediaStatus.Distrus
            : MediaStatus.Sanitizat;

        var pvHtml = GenerateDestructionPvHtml(asset, certNumber, requested, operatorUsername, verifierUsername);

        return new SanitizationResult(
            true,
            certNumber,
            $"Proces-Verbal de Distrugere/Igienizare emis: {certNumber}. Metoda {requested.ToStandardDescription()} a fost executată cu succes!",
            requested,
            pvHtml
        );
    }

    private static string GenerateDestructionPvHtml(MediaAsset med, string pvNumber, SanitizationMethod method, string opName, string witnessName)
    {
        var nowStr = DateTime.UtcNow.ToString("dd.MM.yyyy HH:mm:ss") + " UTC";
        return $@"<!DOCTYPE html><html lang=""ro""><head><meta charset=""UTF-8""><style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 30px; font-size: 13px; color: #111; }}
        .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px; }}
        table.grid {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        table.grid td, table.grid th {{ border: 1px solid #555; padding: 6px 10px; font-size: 12px; }}
        table.grid th {{ background-color: #f3f4f6; text-align: left; width: 35%; }}
        .semnaturi {{ display: flex; justify-content: space-between; margin-top: 40px; }}
        .semn-box {{ width: 45%; border-top: 1px solid #000; padding-top: 6px; text-align: center; font-size: 12px; }}
        </style></head><body>
        <div class=""header"">
            <h3>ROMÂNIA — MINISTERUL APĂRĂRII NAȚIONALE</h3>
            <h2>PROCES-VERBAL DE DISTRUGERE / IGIENIZARE SUPORTURI DE MEMORIE</h2>
            <p>Nr. Înregistrare: <strong>{pvNumber}</strong> | Data: {nowStr}</p>
            <p>Conform HG 585/2002 Art. 65, NIST SP 800-88 Rev. 2 și IEEE 2883-2022</p>
        </div>

        <p>Comisia constituită din operatorul executant și ofițerul de securitate verificator a procedat la distrugerea / igienizarea criptografică a mediului de stocare:</p>

        <table class=""grid"">
            <tr><th>Denumire Volum & Cod Inventar:</th><td><strong>{med.FriendlyName}</strong> ({med.InventoryCode})</td></tr>
            <tr><th>Tip Mediu & Producător:</th><td>{med.MediaType} — {med.Manufacturer} {med.Model}</td></tr>
            <tr><th>Serie Hardware Firmware (S/N 🔒):</th><td><code>{med.SerialNumber}</code></td></tr>
            <tr><th>Plafon Maxim Clasificare Suportat:</th><td><strong>{med.MaxClassification.ToDisplayName()}</strong></td></tr>
            <tr><th>Metodă de Distrugere Aplicată:</th><td><strong>{method.ToStandardDescription()}</strong></td></tr>
            <tr><th>Stare Curentă Mediu:</th><td><strong>BLOCAT / IGIENIZAT IREVOCABIL</strong></td></tr>
        </table>

        <p><i>Constatare: S-a verificat absența oricăror date reziduale. Cheia de decriptare hardware Media Encryption Key (MEK) a fost distrusă, făcând recuperarea datelor imposibilă conform IEEE 2883-2022.</i></p>

        <div class=""semnaturi"">
            <div class=""semn-box"">
                <strong>OPERATOR EXECUTANT</strong><br><br><br>{opName}<br>Semnătură
            </div>
            <div class=""semn-box"">
                <strong>OFIȚER SECURITATE VERIFICATOR (MARTOR)</strong><br><br><br>{witnessName}<br>Semnătură & Ștampilă
            </div>
        </div>
        </body></html>";
    }
}

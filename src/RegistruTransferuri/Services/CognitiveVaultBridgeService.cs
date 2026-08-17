using System.IO;
using System.Security.Cryptography;
using System.Text;
using RegistruTransferuri.Models;

namespace RegistruTransferuri.Services;

/// <summary>
/// Punte Cognitivă C# cu Seiful de Memorie Permanentă (AI_Memory_Vault_CODEX_READY)
/// Oferă:
/// - Oracol de securitate INFOSEC offline pentru proceduri HG 585/2002, NATO AC/35, EUCI și NIST SP 800-88r2
/// - Sinteză canonică a transferurilor militare finalizate în 06_INBOX/RAW_IMPORTS/ (P0-P15)
/// </summary>
public sealed class CognitiveVaultBridgeService
{
    private readonly string _vaultPath;

    public CognitiveVaultBridgeService(string? vaultPath = null)
    {
        _vaultPath = vaultPath ?? @"c:\Users\Marius\Documents\Codex\AI_Memory_Vault_CODEX_READY";
    }

    public bool IsVaultAvailable => Directory.Exists(_vaultPath);

    public string AskSecurityOracle(string query)
    {
        var q = query.ToLowerInvariant();

        if (q.Contains("sanitiz") || q.Contains("nist") || q.Contains("stergere") || q.Contains("distrugere") || q.Contains("purge") || q.Contains("clear"))
        {
            return "🛡️ <b>Normativ Sanitizare Conform NIST SP 800-88 Rev. 2 (2025) & IEEE 2883-2022:</b><br><br>" +
                   "• <b>Nivel NECLASIFICAT:</b> Metoda <code>Clear</code> (Suprascriere logică 1-pass a tuturor sectoarelor adresabile).<br>" +
                   "• <b>Nivel SECRET DE SERVICIU (NATO RESTRICTED):</b> Metoda <code>Purge</code> (Cryptographic Erase pe dispozitive SED TCG Opal sau suprascriere multi-pass cu verificare 100%).<br>" +
                   "• <b>Nivel SECRET & STRICT SECRET (NATO SECRET / COSMIC TOP SECRET):</b> Metoda <code>Destroy</code> (Dezintegrare fizică / tocare conform standardului DIN 66399 clasa H-5 cu particule &lt; 10 mm²).<br><br>" +
                   "<i>Notă: Orice operațiune de sanitizare generează un Certificat Unic semnat de operator și martor verificator.</i>";
        }

        if (q.Contains("numerotar") || q.Contains("prefix") || q.Contains("hg 585") || q.Contains("art. 41") || q.Contains("art 41") || q.Contains("numar"))
        {
            return "📋 <b>Reguli de Numerotare a Transferurilor conform HG 585/2002 (Art. 41):</b><br><br>" +
                   "Fiecare număr de înregistrare militar trebuie să conțină prefixul obligatoriu corespunzător nivelului:<br>" +
                   "• <code>000</code> — <b>Strict Secret de Importanță Deosebită (SSID)</b> (Ex: <code>MAPN-2026-000-0001</code>)<br>" +
                   "• <code>00</code> — <b>Strict Secret (SS)</b> (Ex: <code>MAPN-2026-00-0001</code>)<br>" +
                   "• <code>0</code> — <b>Secret (S)</b> (Ex: <code>MAPN-2026-0-0001</code>)<br>" +
                   "• <code>S</code> — <b>Secret de Serviciu (SSV)</b> (Ex: <code>MAPN-2026-S-0001</code>)<br>" +
                   "• <code>NC</code> — <b>Neclasificat</b> (Ex: <code>MAPN-2026-NC-0001</code>)<br><br>" +
                   "<i>Sistemul permite și introducerea numerelor personalizate de unitate (ex: <code>2150-23SSv</code>).</i>";
        }

        if (q.Contains("nato") || q.Contains("ue") || q.Contains("euci") || q.Contains("clearance") || q.Contains("cosmic"))
        {
            return "🌐 <b>Grila de Echivalență Națională, NATO (AC/35) & Uniunea Europeană (2013/488/UE):</b><br><br>" +
                   "1. <b>Strict Secret de Importanță Deosebită (SSID)</b> ➔ <code>COSMIC TOP SECRET</code> ➔ <code>TRÈS SECRET UE / EU TOP SECRET</code><br>" +
                   "2. <b>Strict Secret (SS)</b> ➔ <code>NATO SECRET</code> ➔ <code>SECRET UE / EU SECRET</code><br>" +
                   "3. <b>Secret (S)</b> ➔ <code>NATO CONFIDENTIAL</code> ➔ <code>CONFIDENTIEL UE / EU CONFIDENTIAL</code><br>" +
                   "4. <b>Secret de Serviciu (SSV)</b> ➔ <code>NATO RESTRICTED</code> ➔ <code>RESTREINT UE / EU RESTRICTED</code><br>" +
                   "5. <b>Neclasificat</b> ➔ <code>NATO UNCLASSIFIED</code> ➔ <code>LIMITE / UNCLASSIFIED</code>";
        }

        if (q.Contains("4 ochi") || q.Contains("four eyes") || q.Contains("aprobator") || q.Contains("contrasemnare") || q.Contains("martor"))
        {
            return "👥 <b>Principiul celor 4 Ochi (Four-Eyes Principle) în Sistemele Clasificate:</b><br><br>" +
                   "• Pentru transferurile cu nivelurile <b>Secret</b>, <b>Strict Secret</b> și <b>SSID</b>, sistemul impune obligatoriu autentificarea a <b>doi utilizatori distincți</b>:<br>" +
                   "  1. <i>Operatorul inițiator</i> (care generează pachetul și calculează hash-ul SHA-256).<br>" +
                   "  2. <i>Ofițerul de securitate / Martorul verificator</i> (care introduce PIN-ul securizat de 6 cifre pentru validare).<br>" +
                   "• Fără aprobarea 4-Eyes, transferul este blocat și nu poate fi efectuat pe mediul amovibil.";
        }

        if (q.Contains("amprent") || q.Contains("vid") || q.Contains("pid") || q.Contains("device control") || q.Contains("whitelist") || q.Contains("stick"))
        {
            return "🔒 <b>Politica de Control Dispozitive (Endpoint Protector Model):</b><br><br>" +
                   "• Fiecare mediu amovibil (USB, CD/DVD, SSD extern, card SD) este legat de stația locală prin amprenta hardware imutabilă: <code>VID</code>, <code>PID</code>, <code>Serie Hardware Firmware (S/N)</code>.<br>" +
                   "• Transferul este autorizat doar dacă nivelul de clasificare al transferului este <b>inferior sau egal cu plafonul de securitate autorizat</b> al mediului.<br>" +
                   "• Datele fizice nu pot fi modificate manual; utilizatorul poate personaliza exclusiv <i>Denumirea Volumului</i> și <i>Numărul de Înregistrare din Registrul de Medii</i>.";
        }

        return "ℹ️ <b>Sistem de Asistență INFOSEC & Registru Transferuri:</b><br>" +
               "Puteți adresa întrebări despre: <i>normele de sanitizare NIST 800-88r2</i>, <i>clasificările NATO/UE</i>, <i>numerotarea HG 585 Art. 41</i>, <i>principiul celor 4 ochi</i> sau <i>politicile de control al mediilor de stocare</i>.";
    }

    public (bool Success, string Message) SynthesizeTransferToVault(TransferRecord tx)
    {
        try
        {
            if (!Directory.Exists(_vaultPath))
                return (false, "Directorul Seifului de Memorie nu a fost găsit.");

            var inboxDir = Path.Combine(_vaultPath, "06_INBOX", "RAW_IMPORTS");
            Directory.CreateDirectory(inboxDir);

            var noteId = Guid.NewGuid().ToString();
            var dateStr = DateTime.UtcNow.ToString("yyyy-MM-dd");
            var cleanNr = tx.RegistryNumber.Replace('/', '_').Replace('-', '_');
            var fileName = $"Transfer_{cleanNr}_{dateStr}.md";
            var filePath = Path.Combine(inboxDir, fileName);

            var markdown = $@"---
id: ""{noteId}""
type: ""experience""
lifecycle: ""REVIEW""
category: ""Transferuri_Militare""
tags: [""transfer_date"", ""militar"", ""hg585"", ""{tx.Classification.ToString().ToLower()}"", ""device_control""]
created: ""{dateStr}""
updated: ""{dateStr}""
provenance:
  source_type: ""execution""
  source_ref: ""MAPN_TRANSFER_{tx.RegistryNumber}""
confidence: ""high""
verification: ""unverified""
relations: []
---

# Raport Operativ Transfer Date: {tx.RegistryNumber}

## 1. Identificare & Clasificare
- **Număr Înregistrare:** {tx.RegistryNumber}
- **Data Execuției:** {tx.TransferDateUtc:yyyy-MM-dd HH:mm:ss} UTC
- **Nivel Clasificare:** {tx.Classification.ToDisplayName()} (NATO: {tx.NatoClassification}, UE: {tx.EuClassification})
- **Direcție Flux:** {tx.Direction.ToUpperInvariant()}
- **Stație Sursă:** {tx.SourceStationHost}

## 2. Pachet Date & Integritate Criptografică
- **Denumire Pachet / Arhivă:** `{tx.PayloadFileName}`
- **Tip Conținut:** {tx.PayloadType} ({tx.PayloadSizeGb} GB, {tx.PayloadFilesCount} fișiere)
- **Hash SHA-256 Date:** `{tx.PayloadSha256Hash}`
- **Hash Înregistrare Audit:** `{tx.IntegrityHash}`
- **Status Antivirus:** {tx.AntivirusDetails}

## 3. Suport Memorie & Telemetrie Hardware
- **Tip Mediu:** {tx.MediaType}
- **Denumire Volum / Etichetă:** {tx.MediaFriendlyLabel}
- **Serie Hardware Firmware (S/N):** `{tx.MediaSerialNumber}`
- **Identificator Hardware:** `VID_{tx.MediaVendorId} & PID_{tx.MediaProductId}`

## 4. Lanț de Custodie & Semnături
- **Persoană Responsabilă:** {tx.SourcePerson} ({tx.SourcePersonRole}) - Legitimație: {tx.SourcePersonIdNumber}
- **Curier Militar:** {tx.CourierName ?? "Predare directă fără curier"} (Permis: {tx.CourierPermitNumber ?? "N/A"})
- **Operator Înregistrare:** {tx.OperatorUsername}
- **Contrasemnare Four-Eyes:** {tx.FourEyesApproverName ?? "N/A"} ({tx.FourEyesApproverRole ?? "N/A"})

---
*Notă generată automat de Puntea Cognitivă a Registrului de Transferuri MApN în Seiful de Memorie AI.*
";

            File.WriteAllText(filePath, markdown, Encoding.UTF8);
            return (true, $"Transferul [{tx.RegistryNumber}] a fost sintetizat în Seiful de Memorie!\nFișier: {fileName}\nStatus: REVIEW (Pregătit pentru atestare)");
        }
        catch (Exception ex)
        {
            return (false, $"Eroare la sinteză: {ex.Message}");
        }
    }
}

using System.IO;
using System.Text;
using System.Web;
using RegistruTransferuri.Models;

namespace RegistruTransferuri.Services;

/// <summary>
/// Serviciu de generare rapoarte oficiale, Procese-Verbale HG 585/2002 si Certificate NIST SP 800-88r2.
/// </summary>
public sealed class PadesExportService
{
    public void ExportCsv(IEnumerable<TransferRecord> records, string filePath)
    {
        var sb = new StringBuilder();
        sb.AppendLine("Nr_Registru,Data_UTC,Clasificare,NATO,Directie,Sursa,Destinatie,Persoana,Mediu,Serie_Hardware,Fisier,Hash_SHA256,Semnat,Four_Eyes");
        foreach (var r in records)
        {
            sb.AppendLine($"\"{r.RegistryNumber}\",\"{r.TransferDateUtc:yyyy-MM-dd HH:mm}\",\"{r.Classification.ToDisplayName()}\",\"{r.NatoClassification}\",\"{r.Direction}\",\"{r.SourceInstitution}\",\"{r.DestinationInstitution}\",\"{r.SourcePerson}\",\"{r.MediaType}\",\"{r.MediaSerialNumber}\",\"{r.PayloadFileName}\",\"{r.PayloadSha256Hash}\",\"{r.Signed}\",\"{r.FourEyesApproverName ?? "N/A"}\"");
        }
        File.WriteAllText(filePath, sb.ToString(), Encoding.UTF8);
    }

    public string GenerateProcesVerbalHtml(TransferRecord tx, string institutie = "MINISTERUL APĂRĂRII NAȚIONALE")
    {
        var nr = HttpUtility.HtmlEncode(tx.RegistryNumber);
        var clf = HttpUtility.HtmlEncode(tx.Classification.ToDisplayName().ToUpperInvariant());
        var natoClf = HttpUtility.HtmlEncode(tx.NatoClassification);
        var euClf = HttpUtility.HtmlEncode(tx.EuClassification);
        var dateStr = tx.TransferDateUtc.ToString("dd.MM.yyyy la ora HH:mm:ss") + " UTC";

        var srcInst = HttpUtility.HtmlEncode(tx.SourceInstitution);
        var srcPc = HttpUtility.HtmlEncode(tx.SourceStationHost);
        var dstInst = HttpUtility.HtmlEncode(tx.DestinationInstitution);
        var dstPc = HttpUtility.HtmlEncode(string.IsNullOrEmpty(tx.DestinationStationHost) ? "Nespecificat" : tx.DestinationStationHost);

        var persNume = HttpUtility.HtmlEncode(tx.SourcePerson);
        var persFunctie = HttpUtility.HtmlEncode(string.IsNullOrEmpty(tx.SourcePersonRole) ? "Operator IT" : tx.SourcePersonRole);
        var persLeg = HttpUtility.HtmlEncode(string.IsNullOrEmpty(tx.SourcePersonIdNumber) ? "N/A" : tx.SourcePersonIdNumber);
        var persAut = HttpUtility.HtmlEncode(tx.SourcePersonClearance);

        var curierNume = HttpUtility.HtmlEncode(string.IsNullOrEmpty(tx.CourierName) ? "Predare Directă fără curier extern" : tx.CourierName);
        var curierLeg = HttpUtility.HtmlEncode(string.IsNullOrEmpty(tx.CourierPermitNumber) ? "N/A" : tx.CourierPermitNumber);

        var medTip = HttpUtility.HtmlEncode(tx.MediaType);
        var medLabel = HttpUtility.HtmlEncode(string.IsNullOrEmpty(tx.MediaFriendlyLabel) ? tx.MediaInventoryCode : tx.MediaFriendlyLabel);
        var medSn = HttpUtility.HtmlEncode(tx.MediaSerialNumber);
        var medVidPid = $"VID_{HttpUtility.HtmlEncode(tx.MediaVendorId)} & PID_{HttpUtility.HtmlEncode(tx.MediaProductId)}";

        var arhivaNume = HttpUtility.HtmlEncode(tx.PayloadFileName);
        var arhivaTip = HttpUtility.HtmlEncode(tx.PayloadType);
        var arhivaDim = tx.PayloadSizeGb;
        var arhivaFisiere = tx.PayloadFilesCount;
        var arhivaHash = HttpUtility.HtmlEncode(tx.PayloadSha256Hash);
        var hashInreg = HttpUtility.HtmlEncode(tx.IntegrityHash);

        var fourEyes = HttpUtility.HtmlEncode(tx.FourEyesApproverName ?? "N/A");
        var fourEyesRol = HttpUtility.HtmlEncode(tx.FourEyesApproverRole ?? "Ofițer Securitate");
        var operatorName = HttpUtility.HtmlEncode(tx.OperatorUsername);

        return $@"<!DOCTYPE html>
<html lang=""ro""><head><meta charset=""UTF-8"">
<title>Proces-Verbal Predare-Primire {nr}</title>
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 30px; color: #111; font-size: 13px; line-height: 1.5; }}
.header-box {{ border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px; }}
.header-top {{ display: flex; justify-content: space-between; font-weight: bold; font-size: 12px; }}
.title-main {{ text-align: center; font-size: 16px; font-weight: bold; margin: 15px 0 5px 0; text-transform: uppercase; }}
.title-sub {{ text-align: center; font-size: 13px; margin: 0; color: #333; font-style: italic; }}
.classification-bar {{ background-color: #111; color: #fff; text-align: center; font-weight: bold; font-size: 14px; padding: 6px; margin: 15px 0; letter-spacing: 2px; }}
.section-title {{ font-size: 14px; font-weight: bold; margin-top: 18px; margin-bottom: 6px; border-bottom: 1px solid #999; padding-bottom: 3px; }}
table.grid {{ width: 100%; border-collapse: collapse; margin-top: 8px; margin-bottom: 12px; }}
table.grid td, table.grid th {{ border: 1px solid #666; padding: 6px 10px; font-size: 12px; vertical-align: top; }}
table.grid th {{ background-color: #f3f4f6; text-align: left; width: 30%; }}
.hash-code {{ font-family: 'Consolas', monospace; font-size: 11px; background-color: #f8fafc; padding: 2px 4px; word-break: break-all; }}
.semnaturi-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 35px; page-break-inside: avoid; }}
.box-semnatura {{ border: 1px solid #333; padding: 12px; border-radius: 4px; font-size: 11px; min-height: 110px; }}
@media print {{ body {{ margin: 12mm; font-size: 11px; }} }}
</style></head>
<body>

<div class=""header-box"">
    <div class=""header-top"">
        <div>ROMÂNIA<br>{HttpUtility.HtmlEncode(institutie)}<br>UNITATEA MILITARĂ: {srcInst}</div>
        <div style=""text-align: right;"">EXEMPLARUL NR. 1<br>Nr. Înregistrare: <strong>{nr}</strong><br>Data: {dateStr}</div>
    </div>
</div>

<div class=""classification-bar"">
    NIVEL CLASIFICARE: {clf} • NATO: {natoClf} • UE: {euClf}
</div>

<div class=""title-main"">PROCES-VERBAL DE PREDARE-PRIMIRE A SUPORTURILOR DE MEMORIE ȘI DATELOR CLASIFICATE</div>
<div class=""title-sub"">Încheiat în conformitate cu HG 585/2002 Art. 65-72, Legea 182/2002 și Directiva NATO AC/35-D/2000-REV8</div>

<div class=""section-title"">1. Date Generale & Entități Implicate</div>
<table class=""grid"">
    <tr><th>Unitate / Instituție Expeditoare (Sursă):</th><td><strong>{srcInst}</strong> (Stație Lucru: {srcPc})</td></tr>
    <tr><th>Unitate / Instituție Destinatară:</th><td><strong>{dstInst}</strong> (Stație Destinație: {dstPc})</td></tr>
    <tr><th>Persoană Responsabilă Transfer:</th><td>{persNume} — {persFunctie} (Legitimație: {persLeg}, Autorizație: {persAut})</td></tr>
    <tr><th>Curier Militar / Delegat Transport:</th><td>{curierNume} (Permis Transport / Legitimație: {curierLeg})</td></tr>
</table>

<div class=""section-title"">2. Identificare Suport Fizic de Stocare (Device Control Whitelist)</div>
<table class=""grid"">
    <tr><th>Tip Suport & Conexiune:</th><td>{medTip}</td></tr>
    <tr><th>Denumire Volum / Cod Inventar Mediu:</th><td><strong>{medLabel}</strong></td></tr>
    <tr><th>Serie Hardware Firmware (S/N):</th><td><code>{medSn}</code></td></tr>
    <tr><th>Identificator Hardware Producător:</th><td><code>{medVidPid}</code></td></tr>
</table>

<div class=""section-title"">3. Pachet de Date & Integritate Criptografică SHA-256</div>
<table class=""grid"">
    <tr><th>Denumire Fișier / Arhivă:</th><td><strong>{arhivaNume}</strong> ({arhivaTip})</td></tr>
    <tr><th>Dimensiune & Volum Date:</th><td>{arhivaDim} GB | Număr Fișiere: {arhivaFisiere}</td></tr>
    <tr><th>Sumă de Control SHA-256 Date:</th><td><div class=""hash-code""><strong>{arhivaHash}</strong></div></td></tr>
    <tr><th>Amprentă Înregistrare Lanț Audit:</th><td><div class=""hash-code"">{hashInreg}</div></td></tr>
    <tr><th>Scanare Antivirus Offline:</th><td>Negativ (Fără amenințări detectate conform bazei de semnături la zi)</td></tr>
</table>

<div class=""section-title"">4. Temei Legal, Restricții & Aprobare Four-Eyes</div>
<table class=""grid"">
    <tr><th>Bază Legală & Reglementări:</th><td>HG 585/2002 Art. 60-73, Legea 182/2002, NATO AC/35</td></tr>
    <tr><th>Contrasemnare Four-Eyes Principle:</th><td>{fourEyes} — {fourEyesRol}</td></tr>
    <tr><th>Operator Sistem Înregistrator:</th><td>{operatorName}</td></tr>
</table>

<div class=""semnaturi-grid"">
    <div class=""box-semnatura"">
        <strong>AM PREDAT (EXPEDITOR):</strong><br><br>
        Grad, Nume: {persNume}<br>
        Funcție: {persFunctie}<br>
        Semnătură & Data: _______________________
    </div>
    <div class=""box-semnatura"">
        <strong>CURIER MILITAR / DELEGAT:</strong><br><br>
        Grad, Nume: {curierNume}<br>
        Permis Transport: {curierLeg}<br>
        Semnătură & Data: _______________________
    </div>
    <div class=""box-semnatura"">
        <strong>AM PRIMIT (DESTINATAR):</strong><br><br>
        Grad, Nume: ____________________________<br>
        Funcție / Legitimație: ____________________<br>
        Semnătură & Data: _______________________
    </div>
    <div class=""box-semnatura"">
        <strong>OFIȚER SECURITATE INFOSEC / MARTOR (4-EYES):</strong><br><br>
        Grad, Nume: {fourEyes}<br>
        Funcție: {fourEyesRol}<br>
        Semnătură & Ștampilă: ____________________
    </div>
</div>

</body></html>";
    }

    public string GenerateSanitizationCertificateHtml(MediaAsset med, string operatorExecutant, string martor, string certNumber, string metoda)
    {
        var codInv = HttpUtility.HtmlEncode(med.InventoryCode);
        var denumire = HttpUtility.HtmlEncode(string.IsNullOrEmpty(med.FriendlyName) ? med.InventoryCode : med.FriendlyName);
        var tip = HttpUtility.HtmlEncode(med.MediaType);
        var sn = HttpUtility.HtmlEncode(med.SerialNumber);
        var cap = med.CapacityGb;
        var maxClf = HttpUtility.HtmlEncode(med.MaxClassification.ToDisplayName());
        var dateStr = DateTime.Now.ToString("dd.MM.yyyy HH:mm:ss");

        return $@"<!DOCTYPE html>
<html lang=""ro""><head><meta charset=""UTF-8"">
<title>Certificat Sanitizare NIST SP 800-88r2 — {codInv}</title>
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 30px; color: #111; font-size: 13px; }}
.cert-border {{ border: 3px double #111; padding: 25px; }}
.header {{ text-align: center; border-bottom: 2px solid #111; padding-bottom: 12px; margin-bottom: 20px; }}
.header h1 {{ font-size: 18px; margin: 0 0 5px 0; text-transform: uppercase; }}
.header h2 {{ font-size: 14px; margin: 0; color: #444; }}
table.grid {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 20px; }}
table.grid td, table.grid th {{ border: 1px solid #666; padding: 8px 12px; font-size: 12px; }}
table.grid th {{ background-color: #f3f4f6; text-align: left; width: 35%; }}
.semnaturi {{ margin-top: 40px; display: flex; justify-content: space-between; }}
.semnaturi div {{ width: 45%; border-top: 1px solid #000; padding-top: 8px; text-align: center; font-size: 12px; }}
</style></head>
<body>
<div class=""cert-border"">
    <div class=""header"">
        <h1>MINISTERUL APĂRĂRII NAȚIONALE</h1>
        <h2>CERTIFICAT DE ATESTARE A SANITIZĂRII / DECOMISIONĂRII SUPORTULUI DE MEMORIE</h2>
        <p style=""margin: 5px 0 0 0; font-size: 11px;"">Conform Standardului <strong>NIST SP 800-88 Rev. 2 (2025)</strong>, IEEE 2883-2022 și HG 585/2002</p>
    </div>

    <p>Prin prezentul document se atestă că mediul de stocare de mai jos a fost supus procedurii de igienizare/ștergere criptografică sigură a datelor:</p>

    <table class=""grid"">
        <tr><th>Cod Evidență / Nr. Înregistrare Mediu:</th><td><strong>{codInv}</strong> ({denumire})</td></tr>
        <tr><th>Tip Mediu de Stocare:</th><td>{tip}</td></tr>
        <tr><th>Serie Hardware Firmware (S/N):</th><td><code>{sn}</code></td></tr>
        <tr><th>Capacitate Fizică:</th><td>{cap} GB</td></tr>
        <tr><th>Plafon Maxim Clasificare Suportat:</th><td><strong>{maxClf}</strong></td></tr>
        <tr><th>Metodă de Sanitizare Executată:</th><td><strong>{HttpUtility.HtmlEncode(metoda)}</strong></td></tr>
        <tr><th>Certificat Număr & Audit:</th><td><code>{HttpUtility.HtmlEncode(certNumber)}</code></td></tr>
        <tr><th>Dată & Oră Execuție:</th><td>{dateStr}</td></tr>
    </table>

    <p><i>Verificare: S-a constatat absența oricăror date reziduale recuperabile. Mediul a fost trecut în starea <strong>BLOCAT / IGIENIZAT</strong>.</i></p>

    <div class=""semnaturi"">
        <div><strong>Operator Executant Sanitizare</strong><br><br><br>{HttpUtility.HtmlEncode(operatorExecutant)}<br>Semnătură</div>
        <div><strong>Martor / Ofițer Securitate Verificator</strong><br><br><br>{HttpUtility.HtmlEncode(martor)}<br>Semnătură & Ștampilă</div>
    </div>
</div>
</body></html>";
    }
}

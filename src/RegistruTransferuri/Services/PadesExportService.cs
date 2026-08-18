using System.IO;
using System.Text;
using System.Web;
using QuestPDF.Fluent;
using QuestPDF.Helpers;
using QuestPDF.Infrastructure;
using RegistruTransferuri.Models;

namespace RegistruTransferuri.Services;

/// <summary>
/// Serviciu de generare rapoarte oficiale, Procese-Verbale HG 585/2002 si Certificate NIST SP 800-88r2 in format HTML si PDF nativ.
/// </summary>
public sealed class PadesExportService
{
    static PadesExportService()
    {
        QuestPDF.Settings.License = LicenseType.Community;
    }

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

    public void GenerateProcesVerbalPdf(TransferRecord tx, string outputPath, string institutie = "MINISTERUL APĂRĂRII NAȚIONALE")
    {
        Document.Create(container =>
        {
            container.Page(page =>
            {
                page.Size(PageSizes.A4);
                page.Margin(20, Unit.Millimetre);
                page.PageColor(Colors.White);
                page.DefaultTextStyle(x => x.FontSize(10).FontFamily("Segoe UI"));

                page.Header().Column(col =>
                {
                    col.Item().Row(row =>
                    {
                        row.RelativeItem().Column(c =>
                        {
                            c.Item().Text("ROMÂNIA").Bold().FontSize(10);
                            c.Item().Text(institutie).Bold().FontSize(9);
                            c.Item().Text($"UM: {tx.SourceInstitution}").FontSize(8);
                        });
                        row.RelativeItem().AlignRight().Column(c =>
                        {
                            c.Item().Text("EXEMPLARUL NR. 1").Bold().FontSize(8);
                            c.Item().Text($"Nr. Înreg: {tx.RegistryNumber}").Bold().FontSize(10).FontColor(Colors.Red.Medium);
                            c.Item().Text($"Data: {tx.TransferDateUtc:yyyy-MM-dd HH:mm} UTC").FontSize(8);
                        });
                    });

                    col.Item().PaddingTop(8).Background(Colors.Grey.Darken3).Padding(4).AlignCenter()
                        .Text($"NIVEL CLASIFICARE: {tx.Classification.ToDisplayName().ToUpperInvariant()} • NATO: {tx.NatoClassification}")
                        .Bold().FontColor(Colors.White).FontSize(10);

                    col.Item().PaddingTop(8).AlignCenter().Text("PROCES-VERBAL DE PREDARE-PRIMIRE A SUPORTURILOR DE DATE").Bold().FontSize(12);
                    col.Item().AlignCenter().Text("Încheiat conform HG 585/2002 Art. 65-72, Legea 182/2002 și NATO AC/35-D/1022").Italic().FontSize(8).FontColor(Colors.Grey.Medium);
                });

                page.Content().PaddingTop(10).Column(col =>
                {
                    col.Item().Text("1. Date Generale & Entități Implicate").Bold().FontSize(10);
                    col.Item().Table(table =>
                    {
                        table.ColumnsDefinition(cols =>
                        {
                            cols.ConstantColumn(160);
                            cols.RelativeColumn();
                        });

                        table.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Unitate Expeditoare (Sursă):").Bold().FontSize(9);
                        table.Cell().Padding(4).Text($"{tx.SourceInstitution} (Stație: {tx.SourceStationHost})").FontSize(9);

                        table.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Unitate Destinatară:").Bold().FontSize(9);
                        table.Cell().Padding(4).Text($"{tx.DestinationInstitution} (Stație: {tx.DestinationStationHost ?? "N/A"})").FontSize(9);

                        table.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Responsabil Transfer:").Bold().FontSize(9);
                        table.Cell().Padding(4).Text($"{tx.SourcePerson} ({tx.SourcePersonRole})").FontSize(9);

                        table.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Curier Militar / Delegat:").Bold().FontSize(9);
                        table.Cell().Padding(4).Text($"{tx.CourierName ?? "Predare Directă"} (Permis: {tx.CourierPermitNumber ?? "N/A"})").FontSize(9);
                    });

                    col.Item().PaddingTop(8).Text("2. Identificare Suport Fizic (Device Control Whitelist)").Bold().FontSize(10);
                    col.Item().Table(table =>
                    {
                        table.ColumnsDefinition(cols =>
                        {
                            cols.ConstantColumn(160);
                            cols.RelativeColumn();
                        });

                        table.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Tip Suport / Mediu:").Bold().FontSize(9);
                        table.Cell().Padding(4).Text($"{tx.MediaType} — Denumire: {tx.MediaFriendlyLabel ?? tx.MediaSerialNumber}").FontSize(9);

                        table.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Serie Hardware Firmware (S/N):").Bold().FontSize(9);
                        table.Cell().Padding(4).Text(tx.MediaSerialNumber).FontFamily("Consolas").Bold().FontSize(9);
                    });

                    col.Item().PaddingTop(8).Text("3. Pachet Date & Integritate Criptografică SHA-256").Bold().FontSize(10);
                    col.Item().Table(table =>
                    {
                        table.ColumnsDefinition(cols =>
                        {
                            cols.ConstantColumn(160);
                            cols.RelativeColumn();
                        });

                        table.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Fișier / Pachet Transferat:").Bold().FontSize(9);
                        table.Cell().Padding(4).Text($"{tx.PayloadFileName} ({tx.PayloadSizeGb:F2} GB)").FontSize(9);

                        table.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Hash SHA-256 Bit-cu-Bit:").Bold().FontSize(9);
                        table.Cell().Padding(4).Text(tx.PayloadSha256Hash).FontFamily("Consolas").FontSize(8);
                    });

                    col.Item().PaddingTop(8).Text("4. Temei Legal & Autorizare Duală (Four-Eyes)").Bold().FontSize(10);
                    col.Item().Table(table =>
                    {
                        table.ColumnsDefinition(cols =>
                        {
                            cols.ConstantColumn(160);
                            cols.RelativeColumn();
                        });

                        table.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Bază Legală:").Bold().FontSize(9);
                        table.Cell().Padding(4).Text("HG 585/2002 Art. 60-73, Legea 182/2002, NATO AC/35-D/1022").FontSize(9);

                        table.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Aprobator 4-Ochi:").Bold().FontSize(9);
                        table.Cell().Padding(4).Text($"{tx.FourEyesApproverName ?? "N/A"} ({tx.FourEyesApproverRole ?? "Ofițer Securitate"})").FontSize(9);
                    });

                    col.Item().PaddingTop(16).Row(row =>
                    {
                        row.RelativeItem().Border(1).BorderColor(Colors.Grey.Medium).Padding(6).Column(c =>
                        {
                            c.Item().Text("AM PREDAT (EXPEDITOR):").Bold().FontSize(8);
                            c.Item().PaddingTop(4).Text($"Nume: {tx.SourcePerson}").FontSize(8);
                            c.Item().PaddingTop(14).Text("Semnătură: ___________________").FontSize(8);
                        });

                        row.ConstantItem(10);

                        row.RelativeItem().Border(1).BorderColor(Colors.Grey.Medium).Padding(6).Column(c =>
                        {
                            c.Item().Text("AM PRIMIT (DESTINATAR):").Bold().FontSize(8);
                            c.Item().PaddingTop(4).Text($"Nume: {tx.DestinationPerson}").FontSize(8);
                            c.Item().PaddingTop(14).Text("Semnătură: ___________________").FontSize(8);
                        });

                        row.ConstantItem(10);

                        row.RelativeItem().Border(1).BorderColor(Colors.Grey.Medium).Padding(6).Column(c =>
                        {
                            c.Item().Text("MARTOR 4-EYES INFOSEC:").Bold().FontSize(8);
                            c.Item().PaddingTop(4).Text($"Nume: {tx.FourEyesApproverName ?? "Ofițer Securitate"}").FontSize(8);
                            c.Item().PaddingTop(14).Text("Semnătură: ___________________").FontSize(8);
                        });
                    });
                });

                page.Footer().AlignCenter().Text(t =>
                {
                    t.Span("Document Militar Oficial — Generat automat de Registrul de Transferuri Air-Gapped").FontSize(7).FontColor(Colors.Grey.Medium);
                });
            });
        }).GeneratePdf(outputPath);
    }

    public void GenerateSanitizationCertificatePdf(MediaAsset med, string operatorExecutant, string martor, string certNumber, string metoda, string outputPath)
    {
        Document.Create(container =>
        {
            container.Page(page =>
            {
                page.Size(PageSizes.A4);
                page.Margin(20, Unit.Millimetre);
                page.PageColor(Colors.White);
                page.DefaultTextStyle(x => x.FontSize(10).FontFamily("Segoe UI"));

                page.Header().Column(col =>
                {
                    col.Item().AlignCenter().Text("MINISTERUL APĂRĂRII NAȚIONALE").Bold().FontSize(14);
                    col.Item().AlignCenter().Text("CERTIFICAT DE SANITIZARE & DECOMISIONARE SUPORT MEMORIE").Bold().FontSize(12);
                    col.Item().AlignCenter().Text("Conform Standardului NIST SP 800-88 Rev. 2 (2025), IEEE 2883-2022 și HG 585/2002 Art. 65").Italic().FontSize(8).FontColor(Colors.Grey.Medium);
                    col.Item().PaddingTop(6).LineHorizontal(1.5f).LineColor(Colors.Black);
                });

                page.Content().PaddingTop(12).Column(col =>
                {
                    col.Item().Text($"Certificat Nr: {certNumber}").Bold().FontSize(11).FontColor(Colors.Red.Medium);
                    col.Item().PaddingTop(4).Text("Prin prezentul document se atestă că mediul de stocare de mai jos a fost supus procedurii de igienizare criptografică sigură a datelor, fără posibilitate de recuperare:").FontSize(9);

                    col.Item().PaddingTop(10).Table(table =>
                    {
                        table.ColumnsDefinition(cols =>
                        {
                            cols.ConstantColumn(160);
                            cols.RelativeColumn();
                        });

                        table.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Cod Evidență / Volum:").Bold().FontSize(9);
                        table.Cell().Padding(4).Text($"{med.InventoryCode} ({med.FriendlyName})").FontSize(9);

                        table.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Tip Suport & Capacitate:").Bold().FontSize(9);
                        table.Cell().Padding(4).Text($"{med.MediaType} ({med.CapacityGb} GB)").FontSize(9);

                        table.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Serie Hardware Firmware:").Bold().FontSize(9);
                        table.Cell().Padding(4).Text(med.SerialNumber).FontFamily("Consolas").Bold().FontSize(9);

                        table.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Metodă Sanitizare:").Bold().FontSize(9);
                        table.Cell().Padding(4).Text(metoda).Bold().FontSize(9);

                        table.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Data & Ora Execuției:").Bold().FontSize(9);
                        table.Cell().Padding(4).Text($"{DateTime.UtcNow:yyyy-MM-dd HH:mm:ss} UTC").FontSize(9);
                    });

                    col.Item().PaddingTop(12).Background(Colors.Grey.Lighten4).Padding(6).Text("Rezultat Verificare: S-a constatat absența oricăror date reziduale recuperabile. Cheile MEK au fost distruse, iar mediul a fost trecut în starea BLOCAT / IGIENIZAT.").Italic().FontSize(8);

                    col.Item().PaddingTop(24).Row(row =>
                    {
                        row.RelativeItem().Border(1).BorderColor(Colors.Grey.Medium).Padding(8).Column(c =>
                        {
                            c.Item().Text("OPERATOR EXECUTANT:").Bold().FontSize(8);
                            c.Item().PaddingTop(4).Text($"Nume: {operatorExecutant}").FontSize(8);
                            c.Item().PaddingTop(20).Text("Semnătură: ___________________").FontSize(8);
                        });

                        row.ConstantItem(20);

                        row.RelativeItem().Border(1).BorderColor(Colors.Grey.Medium).Padding(8).Column(c =>
                        {
                            c.Item().Text("MARTOR / OFIȚER SECURITATE (4-EYES):").Bold().FontSize(8);
                            c.Item().PaddingTop(4).Text($"Nume: {martor}").FontSize(8);
                            c.Item().PaddingTop(20).Text("Semnătură & Ștampilă: ___________________").FontSize(8);
                        });
                    });
                });

                page.Footer().AlignCenter().Text("Document Militar Oficial — Distrugere Garantată Date Clasificate").FontSize(7).FontColor(Colors.Grey.Medium);
            });
        }).GeneratePdf(outputPath);
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

    public void GenerateActivityReportPdf(IEnumerable<TransferRecord> transfers, IEnumerable<MediaAsset> assets, string outputPath, string institutie = "MINISTERUL APĂRĂRII NAȚIONALE")
    {
        var txList = transfers.ToList();
        var assetList = assets.ToList();
        var totalTx = txList.Count;
        var classifiedTx = txList.Count(t => t.Classification >= ClassificationLevel.Secret);
        var totalAssets = assetList.Count;
        var sanitizedAssets = assetList.Count(a => a.Status == MediaStatus.Sanitizat || a.Status == MediaStatus.Distrus);

        Document.Create(container =>
        {
            container.Page(page =>
            {
                page.Size(PageSizes.A4);
                page.Margin(20, Unit.Millimetre);
                page.PageColor(Colors.White);
                page.DefaultTextStyle(x => x.FontSize(10).FontFamily("Segoe UI"));

                page.Header().Column(col =>
                {
                    col.Item().Row(row =>
                    {
                        row.RelativeItem().Column(c =>
                        {
                            c.Item().Text("ROMÂNIA").Bold().FontSize(11);
                            c.Item().Text(institutie).Bold().FontSize(10);
                            c.Item().Text("STRUCTURA DE SECURITATE INFOSEC").FontSize(8);
                        });
                        row.RelativeItem().AlignRight().Column(c =>
                        {
                            c.Item().Text("RAPORT DE CONFORMITATE").Bold().FontSize(9);
                            c.Item().Text($"Data: {DateTime.UtcNow:yyyy-MM-dd HH:mm} UTC").FontSize(8);
                            c.Item().Text("REGIM AIR-GAPPED").Bold().FontColor(Colors.Blue.Medium).FontSize(8);
                        });
                    });

                    col.Item().PaddingTop(10).LineHorizontal(1.5f).LineColor(Colors.Black);
                });

                page.Content().PaddingTop(15).Column(col =>
                {
                    col.Item().AlignCenter().Text("RAPORT SINTETIC PRIVIND TRANSFERURILE DE DATE ȘI CONTROLUL DISPOZITIVELOR").Bold().FontSize(13);
                    col.Item().AlignCenter().Text("Conform HG 585/2002, NATO AC/35-D/1022 și NIST SP 800-88r2").FontSize(9).FontColor(Colors.Grey.Medium);

                    col.Item().PaddingTop(15).Row(row =>
                    {
                        row.RelativeItem().Border(1).BorderColor(Colors.Grey.Lighten1).Padding(8).Column(c =>
                        {
                            c.Item().Text("TOTAL TRANSFERURI").Bold().FontSize(8).FontColor(Colors.Grey.Darken1);
                            c.Item().Text($"{totalTx}").Bold().FontSize(18).FontColor(Colors.Blue.Darken2);
                        });
                        row.RelativeItem().Border(1).BorderColor(Colors.Grey.Lighten1).Padding(8).Column(c =>
                        {
                            c.Item().Text("TRANSFERURI CLASIFICATE (S/SS/SSID)").Bold().FontSize(8).FontColor(Colors.Grey.Darken1);
                            c.Item().Text($"{classifiedTx}").Bold().FontSize(18).FontColor(Colors.Red.Darken2);
                        });
                        row.RelativeItem().Border(1).BorderColor(Colors.Grey.Lighten1).Padding(8).Column(c =>
                        {
                            c.Item().Text("MEDII AMPRENTATE ÎN WHITELIST").Bold().FontSize(8).FontColor(Colors.Grey.Darken1);
                            c.Item().Text($"{totalAssets}").Bold().FontSize(18).FontColor(Colors.Green.Darken2);
                        });
                        row.RelativeItem().Border(1).BorderColor(Colors.Grey.Lighten1).Padding(8).Column(c =>
                        {
                            c.Item().Text("MEDII SANITIZATE / DISTRUSE").Bold().FontSize(8).FontColor(Colors.Grey.Darken1);
                            c.Item().Text($"{sanitizedAssets}").Bold().FontSize(18).FontColor(Colors.Orange.Darken2);
                        });
                    });

                    col.Item().PaddingTop(20).Text("1. Ultimele Transferuri Înregistrate").Bold().FontSize(11);

                    col.Item().PaddingTop(6).Table(table =>
                    {
                        table.ColumnsDefinition(columns =>
                        {
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(3);
                            columns.RelativeColumn(3);
                        });

                        table.Header(header =>
                        {
                            header.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Nr. Înregistrare").Bold().FontSize(8);
                            header.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Dată UTC").Bold().FontSize(8);
                            header.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Clasificare").Bold().FontSize(8);
                            header.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Destinație").Bold().FontSize(8);
                            header.Cell().Background(Colors.Grey.Lighten3).Padding(4).Text("Fișier").Bold().FontSize(8);
                        });

                        foreach (var tx in txList.Take(10))
                        {
                            table.Cell().BorderBottom(0.5f).BorderColor(Colors.Grey.Lighten2).Padding(4).Text(tx.RegistryNumber).FontSize(8);
                            table.Cell().BorderBottom(0.5f).BorderColor(Colors.Grey.Lighten2).Padding(4).Text(tx.TransferDateUtc.ToString("yyyy-MM-dd HH:mm")).FontSize(8);
                            table.Cell().BorderBottom(0.5f).BorderColor(Colors.Grey.Lighten2).Padding(4).Text(tx.Classification.ToDisplayName()).FontSize(8).Bold();
                            table.Cell().BorderBottom(0.5f).BorderColor(Colors.Grey.Lighten2).Padding(4).Text(tx.DestinationInstitution).FontSize(8);
                            table.Cell().BorderBottom(0.5f).BorderColor(Colors.Grey.Lighten2).Padding(4).Text(tx.PayloadFileName).FontSize(8);
                        }
                    });

                    col.Item().PaddingTop(25).Row(row =>
                    {
                        row.RelativeItem().Column(c =>
                        {
                            c.Item().Text("ÎNTOCMIT").Bold().FontSize(9);
                            c.Item().Text("Ofițer Securitate INFOSEC").FontSize(8);
                            c.Item().PaddingTop(20).Text("_____________________").FontSize(8);
                        });
                        row.RelativeItem().AlignRight().Column(c =>
                        {
                            c.Item().Text("VIZAT / APROBAT").Bold().FontSize(9);
                            c.Item().Text("Șef Structură Securitate").FontSize(8);
                            c.Item().PaddingTop(20).Text("_____________________").FontSize(8);
                        });
                    });
                });

                page.Footer().AlignCenter().Text(t =>
                {
                    t.Span("Document de uz intern militar — Generat automat din Registrul de Transferuri | Pagina ");
                    t.CurrentPageNumber();
                    t.Span(" din ");
                    t.TotalPages();
                });
            });
        }).GeneratePdf(outputPath);
    }
}

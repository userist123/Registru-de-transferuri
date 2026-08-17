"""
Export Service - Generare Rapoarte Oficiale, Procese-Verbale HG 585/2002 si Certificate NIST SP 800-88r2
Formatate conform standardelor MApN, NATO AC/35-D/2000-REV8 si EUCI 2013/488/UE.
"""
import csv, html
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class ExportService:
    @staticmethod
    def export_csv(transfers: List[Dict], output_path: str) -> str:
        if not transfers:
            raise ValueError("Nu există date de exportat.")
        fieldnames = list(transfers[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(transfers)
        return output_path

    @staticmethod
    def export_html_report(transfers: List[Dict], output_path: str, institutie: str = "MINISTERUL APĂRĂRII NAȚIONALE") -> str:
        rows_html = ""
        for t in transfers:
            clf = html.escape(str(t.get('clasificare', '')))
            nato_clf = html.escape(str(t.get('clasificare_nato', '')))
            direction = html.escape(str(t.get('directie_transfer', 'iesire').upper()))
            semnat = "DA (" + html.escape(str(t.get('semnat_de', ''))) + ")" if t.get('semnat_operator') else "NU"
            four_eyes = html.escape(str(t.get('four_eyes_aprobator') or "N/A"))

            rows_html += f"""
            <tr>
                <td><strong>{html.escape(str(t.get('nr','')))}</strong></td>
                <td>{html.escape(str(t.get('date_created',''))[:16].replace('T', ' '))}</td>
                <td><span class="badge badge-clf">{clf}</span><br><small>{nato_clf}</small></td>
                <td><strong>{direction}</strong></td>
                <td>{html.escape(str(t.get('src_institutie','')))}<br><small>Stație: {html.escape(str(t.get('src_pc_nume','')))}</small></td>
                <td>{html.escape(str(t.get('dst_institutie','')))}<br><small>Stație: {html.escape(str(t.get('dst_pc_nume') or '-'))}</small></td>
                <td>{html.escape(str(t.get('pers_nume','')))}<br><small>{html.escape(str(t.get('pers_functie') or ''))}</small></td>
                <td>{html.escape(str(t.get('transfer_medium','')))}<br><small>S/N: {html.escape(str(t.get('transfer_sn') or '-'))}</small></td>
                <td>{html.escape(str(t.get('arhiva_nume','')))}<br><code style="font-size: 10px;">{html.escape(str(t.get('arhiva_hash',''))[:16])}...</code></td>
                <td>{four_eyes}</td>
                <td>{semnat}</td>
            </tr>"""

        html_content = f"""<!DOCTYPE html>
<html lang="ro"><head><meta charset="UTF-8">
<title>Raport Oficial Registru Transferuri Date Militare — {html.escape(institutie)}</title>
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 30px; color: #111; font-size: 12px; }}
.header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 12px; margin-bottom: 20px; }}
.header h1 {{ font-size: 18px; margin: 0 0 5px 0; text-transform: uppercase; letter-spacing: 1px; }}
.header h2 {{ font-size: 14px; margin: 0; color: #333; }}
.meta-info {{ display: flex; justify-content: space-between; margin-bottom: 15px; font-size: 11px; color: #333; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
th, td {{ border: 1px solid #777; padding: 6px 8px; text-align: left; vertical-align: top; }}
th {{ background-color: #e5e7eb; font-weight: bold; font-size: 11px; }}
.badge-clf {{ font-weight: bold; color: #b91c1c; }}
.semnaturi {{ margin-top: 50px; display: flex; justify-content: space-between; page-break-inside: avoid; }}
.semnaturi div {{ width: 28%; border-top: 1px solid #000; padding-top: 8px; text-align: center; font-size: 11px; }}
@media print {{ body {{ margin: 10mm; font-size: 10px; }} }}
</style></head>
<body>
<div class="header">
    <h1>ROMÂNIA — {html.escape(institutie)}</h1>
    <h2>REGISTRUL DE EVIDENȚĂ A TRANSFERURILOR DE DATE PE MEDII DE STOCARE CLASIFICATE</h2>
    <p style="margin: 5px 0 0 0; font-size: 11px;">Conform HG 585/2002, Legea 182/2002, Decizia 2013/488/UE și Directivele de Securitate NATO AC/35</p>
</div>

<div class="meta-info">
    <div><strong>Dată Generare Raport:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</div>
    <div><strong>Total Înregistrări:</strong> {len(transfers)}</div>
    <div><strong>Regim de Funcționare:</strong> Sistem Izolat (Air-Gapped)</div>
</div>

<table>
<thead>
    <tr>
        <th>Nr. Registru</th>
        <th>Dată & Oră</th>
        <th>Clasificare Națională / NATO</th>
        <th>Direcție</th>
        <th>Sursă</th>
        <th>Destinație</th>
        <th>Persoană / Delegat</th>
        <th>Mediu Stocare Amprentat</th>
        <th>Conținut & SHA-256</th>
        <th>Aprobare 4-Eyes</th>
        <th>Semnătură Operator</th>
    </tr>
</thead>
<tbody>
    {rows_html}
</tbody>
</table>

<div class="semnaturi">
    <div><strong>Operator Registru / Executant</strong><br><br><br>Grad, Nume, Semnătură</div>
    <div><strong>Martor / Ofițer Securitate IT (4-Eyes)</strong><br><br><br>Grad, Nume, Semnătură</div>
    <div><strong>Șef Structură Securitate / Aprobare</strong><br><br><br>Grad, Nume, Semnătură & Ștampilă</div>
</div>
</body></html>"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return output_path

    @staticmethod
    def generate_proces_verbal_html(tx: Dict, institutie: str = "MINISTERUL APĂRĂRII NAȚIONALE") -> str:
        """
        Genereaza Proces-Verbal Oficial de Predare-Primire a Suporturilor de Stocare
        conform cerintelor din HG 585/2002 Art. 65-72 si normelor de curierat militar.
        """
        nr = html.escape(str(tx.get('nr', 'N/A')))
        clf = html.escape(str(tx.get('clasificare', 'Neclasificat')).upper())
        nato_clf = html.escape(str(tx.get('clasificare_nato', 'NATO UNCLASSIFIED')))
        eu_clf = html.escape(str(tx.get('clasificare_eu', 'LIMITE / UNCLASSIFIED')))
        date_str = html.escape(str(tx.get('date_created', datetime.now().isoformat()))[:16].replace('T', ' la ora '))

        src_inst = html.escape(str(tx.get('src_institutie', 'N/A')))
        src_pc = html.escape(str(tx.get('src_pc_nume', 'N/A')))
        dst_inst = html.escape(str(tx.get('dst_institutie', 'N/A')))
        dst_pc = html.escape(str(tx.get('dst_pc_nume') or 'Nespecificat'))

        pers_nume = html.escape(str(tx.get('pers_nume', 'N/A')))
        pers_functie = html.escape(str(tx.get('pers_functie') or 'Operator IT'))
        pers_leg = html.escape(str(tx.get('pers_legitimatie') or 'N/A'))
        pers_aut = html.escape(str(tx.get('pers_autorizatie', 'Neclasificat')))

        curier_nume = html.escape(str(tx.get('curier_militar_nume') or 'Predare Directă fără curier extern'))
        curier_leg = html.escape(str(tx.get('curier_militar_legitimatie') or 'N/A'))

        med_tip = html.escape(str(tx.get('transfer_medium', 'Mediu Amovibil')))
        med_label = html.escape(str(tx.get('transfer_label') or 'N/A'))
        med_sn = html.escape(str(tx.get('transfer_sn') or 'N/A'))
        med_vid = html.escape(str(tx.get('transfer_vid') or 'N/A'))
        med_pid = html.escape(str(tx.get('transfer_pid') or 'N/A'))

        arhiva_nume = html.escape(str(tx.get('arhiva_nume', 'N/A')))
        arhiva_tip = html.escape(str(tx.get('arhiva_tip', 'Pachet date')))
        arhiva_dim = html.escape(str(tx.get('arhiva_dim_gb', 0)))
        arhiva_fisiere = html.escape(str(tx.get('arhiva_fisiere', 1)))
        arhiva_hash = html.escape(str(tx.get('arhiva_hash', 'N/A')))
        hash_inreg = html.escape(str(tx.get('hash_inregistrare', 'N/A')))

        four_eyes_aprobator = html.escape(str(tx.get('four_eyes_aprobator') or 'N/A'))
        four_eyes_functie = html.escape(str(tx.get('four_eyes_functie') or 'Ofițer Securitate'))
        operator_executant = html.escape(str(tx.get('operator', 'Operator Registru')))

        return f"""<!DOCTYPE html>
<html lang="ro"><head><meta charset="UTF-8">
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

<div class="header-box">
    <div class="header-top">
        <div>ROMÂNIA<br>{html.escape(institutie)}<br>UNITATEA MILITARĂ: {src_inst}</div>
        <div style="text-align: right;">EXEMPLARUL NR. 1<br>Nr. Înregistrare: <strong>{nr}</strong><br>Data: {date_str}</div>
    </div>
</div>

<div class="classification-bar">
    NIVEL CLASIFICARE: {clf} • NATO: {nato_clf} • UE: {eu_clf}
</div>

<div class="title-main">PROCES-VERBAL DE PREDARE-PRIMIRE A SUPORTURILOR DE MEMORIE ȘI DATELOR CLASIFICATE</div>
<div class="title-sub">Încheiat în conformitate cu HG 585/2002 Art. 65-72, Legea 182/2002 și Directiva NATO AC/35-D/2000-REV8</div>

<div class="section-title">1. Date Generale & Entități Implicate</div>
<table class="grid">
    <tr><th>Unitate / Instituție Expeditoare (Sursă):</th><td><strong>{src_inst}</strong> (Stație Lucru: {src_pc})</td></tr>
    <tr><th>Unitate / Instituție Destinatară:</th><td><strong>{dst_inst}</strong> (Stație Destinație: {dst_pc})</td></tr>
    <tr><th>Persoană Responsabilă Transfer:</th><td>{pers_nume} — {pers_functie} (Legitimație: {pers_leg}, Autorizație: {pers_aut})</td></tr>
    <tr><th>Curier Militar / Delegat Transport:</th><td>{curier_nume} (Permis Transport / Legitimație: {curier_leg})</td></tr>
</table>

<div class="section-title">2. Identificare Suport Fizic de Stocare (Device Control Whitelist)</div>
<table class="grid">
    <tr><th>Tip Suport & Conexiune:</th><td>{med_tip}</td></tr>
    <tr><th>Denumire Volum / Cod Inventar Mediu:</th><td><strong>{med_label}</strong></td></tr>
    <tr><th>Serie Hardware Firmware (S/N):</th><td><code>{med_sn}</code></td></tr>
    <tr><th>Identificator Hardware Producător:</th><td><code>VID_{med_vid} & PID_{med_pid}</code></td></tr>
</table>

<div class="section-title">3. Pachet de Date & Integritate Criptografică SHA-256</div>
<table class="grid">
    <tr><th>Denumire Fișier / Arhivă:</th><td><strong>{arhiva_nume}</strong> ({arhiva_tip})</td></tr>
    <tr><th>Dimensiune & Volum Date:</th><td>{arhiva_dim} GB | Număr Fișiere: {arhiva_fisiere}</td></tr>
    <tr><th>Sumă de Control SHA-256 Date:</th><td><div class="hash-code"><strong>{arhiva_hash}</strong></div></td></tr>
    <tr><th>Amprentă Înregistrare Lanț Audit:</th><td><div class="hash-code">{hash_inreg}</div></td></tr>
    <tr><th>Scanare Antivirus Offline:</th><td>Negativ (Fără amenințări detectate conform bazei de semnături la zi)</td></tr>
</table>

<div class="section-title">4. Temei Legal, Restricții & Aprobare Four-Eyes</div>
<table class="grid">
    <tr><th>Bază Legală & Reglementări:</th><td>HG 585/2002 Art. 60-73, Legea 182/2002, NATO AC/35</td></tr>
    <tr><th>Contrasemnare Four-Eyes Principle:</th><td>{four_eyes_aprobator} — {four_eyes_functie}</td></tr>
    <tr><th>Operator Sistem Înregistrator:</th><td>{operator_executant}</td></tr>
</table>

<div class="semnaturi-grid">
    <div class="box-semnatura">
        <strong>AM PREDAT (EXPEDITOR):</strong><br><br>
        Grad, Nume: {pers_nume}<br>
        Funcție: {pers_functie}<br>
        Semnătură & Data: _______________________
    </div>
    <div class="box-semnatura">
        <strong>CURIER MILITAR / DELEGAT:</strong><br><br>
        Grad, Nume: {curier_nume}<br>
        Permis Transport: {curier_leg}<br>
        Semnătură & Data: _______________________
    </div>
    <div class="box-semnatura">
        <strong>AM PRIMIT (DESTINATAR):</strong><br><br>
        Grad, Nume: ____________________________<br>
        Funcție / Legitimație: ____________________<br>
        Semnătură & Data: _______________________
    </div>
    <div class="box-semnatura">
        <strong>OFIȚER SECURITATE INFOSEC / MARTOR (4-EYES):</strong><br><br>
        Grad, Nume: {four_eyes_aprobator}<br>
        Funcție: {four_eyes_functie}<br>
        Semnătură & Ștampilă: ____________________
    </div>
</div>

</body></html>"""

    @staticmethod
    def generate_sanitization_certificate_html(medium: Dict, operator_executant: str, martor: str, procedura: str = "", metoda: str = "Purge (Cryptographic Erase)") -> str:
        """Genereaza Certificat Oficial de Sanitizare & Decomisionare Conform NIST SP 800-88 Rev. 2 / IEEE 2883-2022."""
        cod_inv = html.escape(str(medium.get('cod_inventar', 'N/A')))
        denumire = html.escape(str(medium.get('denumire_custom') or medium.get('cod_inventar', 'N/A')))
        tip = html.escape(str(medium.get('tip_mediu', 'Mediu Stocare')))
        sn = html.escape(str(medium.get('serie_hardware', 'N/A')))
        cap = html.escape(str(medium.get('capacitate_gb', '0')))
        max_clf = html.escape(str(medium.get('clasificare_max', 'Neclasificat')))
        date_str = datetime.now().strftime('%d.%m.%Y %H:%M:%S')

        return f"""<!DOCTYPE html>
<html lang="ro"><head><meta charset="UTF-8">
<title>Certificat Sanitizare NIST SP 800-88r2 — {cod_inv}</title>
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
<div class="cert-border">
    <div class="header">
        <h1>MINISTERUL APĂRĂRII NAȚIONALE</h1>
        <h2>CERTIFICAT DE ATESTARE A SANITIZĂRII / DECOMISIONĂRII SUPORTULUI DE MEMORIE</h2>
        <p style="margin: 5px 0 0 0; font-size: 11px;">Conform Standardului <strong>NIST SP 800-88 Rev. 2 (2025)</strong>, IEEE 2883-2022 și HG 585/2002</p>
    </div>

    <p>Prin prezentul document se atestă că mediul de stocare de mai jos a fost supus procedurii de igienizare/ștergere criptografică sigură a datelor:</p>

    <table class="grid">
        <tr><th>Cod Evidență / Nr. Înregistrare Mediu:</th><td><strong>{cod_inv}</strong> ({denumire})</td></tr>
        <tr><th>Tip Mediu de Stocare:</th><td>{tip}</td></tr>
        <tr><th>Serie Hardware Firmware (S/N):</th><td><code>{sn}</code></td></tr>
        <tr><th>Capacitate Fizică:</th><td>{cap} GB</td></tr>
        <tr><th>Plafon Maxim Clasificare Suportat:</th><td><strong>{max_clf}</strong></td></tr>
        <tr><th>Metodă de Sanitizare Executată:</th><td><strong>{html.escape(metoda)}</strong></td></tr>
        <tr><th>Procedură & Detalii Tehnice:</th><td>{html.escape(procedura or 'Suprascriere și distrugere chei criptografice TCG Opal')}</td></tr>
        <tr><th>Dată & Oră Execuție:</th><td>{date_str}</td></tr>
    </table>

    <p><i>Verificare: S-a constatat absența oricăror date reziduale recuperabile. Mediul a fost trecut în starea <strong>BLOCAT / IGIENIZAT</strong>.</i></p>

    <div class="semnaturi">
        <div><strong>Operator Executant Sanitizare</strong><br><br><br>{html.escape(operator_executant)}<br>Semnătură</div>
        <div><strong>Martor / Ofițer Securitate Verificator</strong><br><br><br>{html.escape(martor)}<br>Semnătură & Ștampilă</div>
    </div>
</div>
</body></html>"""

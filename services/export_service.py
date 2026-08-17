import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict


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
            clf = t.get('clasificare', '')
            nato_clf = t.get('clasificare_nato', '')
            direction = t.get('directie_transfer', 'iesire').upper()
            semnat = "DA (" + str(t.get('semnat_de', '')) + ")" if t.get('semnat_operator') else "NU"
            four_eyes = t.get('four_eyes_aprobator') or "N/A"

            rows_html += f"""
            <tr>
                <td><strong>{t.get('nr','')}</strong></td>
                <td>{t.get('date_created','')[:16].replace('T', ' ')}</td>
                <td><span class="badge badge-clf">{clf}</span><br><small>{nato_clf}</small></td>
                <td><strong>{direction}</strong></td>
                <td>{t.get('src_institutie','')}<br><small>Stație: {t.get('src_pc_nume','')}</small></td>
                <td>{t.get('dst_institutie','')}<br><small>Stație: {t.get('dst_pc_nume') or '-'}</small></td>
                <td>{t.get('pers_nume','')}<br><small>{t.get('pers_functie') or ''}</small></td>
                <td>{t.get('transfer_medium','')}<br><small>S/N: {t.get('transfer_sn') or '-'}</small></td>
                <td>{t.get('arhiva_nume','')}<br><code style="font-size: 10px;">{t.get('arhiva_hash','')[:16]}...</code></td>
                <td>{four_eyes}</td>
                <td>{semnat}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="ro"><head><meta charset="UTF-8">
<title>Raport Oficial Registru Transferuri Date Militare — {institutie}</title>
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 30px; color: #111; font-size: 12px; }}
.header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 12px; margin-bottom: 20px; }}
.header h1 {{ font-size: 18px; margin: 0 0 5px 0; text-transform: uppercase; }}
.header h2 {{ font-size: 14px; margin: 0; color: #444; }}
.meta-info {{ display: flex; justify-content: space-between; margin-bottom: 15px; font-size: 11px; color: #333; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
th, td {{ border: 1px solid #777; padding: 6px 8px; text-align: left; vertical-align: top; }}
th {{ background-color: #e5e7eb; font-weight: bold; font-size: 11px; }}
.badge-clf {{ font-weight: bold; color: #b91c1c; }}
.semnaturi {{ margin-top: 50px; display: flex; justify-content: space-between; }}
.semnaturi div {{ width: 28%; border-top: 1px solid #000; padding-top: 8px; text-align: center; font-size: 11px; }}
@media print {{ body {{ margin: 10mm; font-size: 10px; }} }}
</style></head>
<body>
<div class="header">
    <h1>ROMÂNIA — {institutie}</h1>
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

        Path(output_path).write_text(html, encoding='utf-8')
        return output_path

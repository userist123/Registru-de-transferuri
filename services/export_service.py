import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict

class ExportService:
    @staticmethod
    def export_csv(transfers: List[Dict], output_path: str) -> str:
        if not transfers:
            raise ValueError("Nu exista date pentru export.")
        
        fieldnames = [
            'nr', 'date_created', 'clasificare', 'status', 'semnat_operator', 'semnat_de',
            'src_institutie', 'src_pc_nume', 'pers_nume', 'pers_autorizatie',
            'transfer_medium', 'transfer_sn', 'dst_institutie', 'dst_pc_nume',
            'arhiva_nume', 'arhiva_hash', 'baza_legala', 'operator', 'hash_inregistrare'
        ]
        
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        
        with open(p, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for t in transfers:
                writer.writerow(t)
        return str(p)

    @staticmethod
    def generate_html_report(transfers: List[Dict], institutie: str, titlu: str = "REGISTRU EVIDENȚĂ TRANSFERURI MEDIA") -> str:
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        
        rows_html = ""
        for t in transfers:
            semn = f"Semnat ({t.get('semnat_de', '')})" if t.get('semnat_operator') else "Nesemnat"
            status_style = "color: #ef4444;" if t.get('status') == 'anulat' else ("color: #10b981;" if t.get('semnat_operator') else "color: #f59e0b;")
            rows_html += f"""
            <tr>
                <td style="font-weight: bold;">{t.get('nr')}</td>
                <td>{t.get('date_created', '')[:19].replace('T', ' ')}</td>
                <td><span class="badge badge-{t.get('clasificare', '').replace(' ', '-').lower()}">{t.get('clasificare')}</span></td>
                <td>{t.get('src_institutie')}<br><small style="color: #64748b;">{t.get('src_pc_nume')}</small></td>
                <td>{t.get('pers_nume')}<br><small style="color: #64748b;">{t.get('pers_autorizatie')}</small></td>
                <td>{t.get('transfer_medium')}<br><small style="color: #64748b;">S/N: {t.get('transfer_sn') or 'N/A'}</small></td>
                <td>{t.get('dst_institutie')}<br><small style="color: #64748b;">{t.get('dst_pc_nume') or ''}</small></td>
                <td>{t.get('arhiva_nume') or 'Direct'}<br><small style="font-family: monospace; font-size: 9px; color: #64748b;">{(t.get('arhiva_hash') or '')[:16]}...</small></td>
                <td style="{status_style}; font-weight: bold;">{t.get('status').upper()}<br><small>{semn}</small></td>
            </tr>
            """

        html = f"""<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="UTF-8">
    <title>{titlu} - {institutie}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 30px; background-color: #f8fafc; color: #1e293b; }}
        .header {{ border-bottom: 2px solid #0f172a; padding-bottom: 15px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; font-size: 20pt; color: #0f172a; text-transform: uppercase; }}
        .header p {{ margin: 5px 0 0; color: #475569; font-size: 11pt; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 10pt; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        th, td {{ border: 1px solid #cbd5e1; padding: 8px 10px; text-align: left; vertical-align: top; }}
        th {{ background-color: #0f172a; color: #fff; font-weight: 600; text-transform: uppercase; font-size: 9pt; }}
        tr:nth-child(even) {{ background-color: #f1f5f9; }}
        .badge {{ padding: 3px 8px; border-radius: 4px; font-size: 8pt; font-weight: bold; display: inline-block; }}
        .badge-neclasificat {{ background: #e2e8f0; color: #334155; }}
        .badge-secret-de-serviciu {{ background: #fef08a; color: #854d0e; }}
        .badge-secret {{ background: #fecaca; color: #991b1b; }}
        .badge-strict-secret {{ background: #e9d5ff; color: #6b21a8; }}
        .badge-strict-secret-de-importanță-deosebită {{ background: #991b1b; color: #ffffff; }}
        .footer {{ margin-top: 40px; font-size: 9pt; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 15px; display: flex; justify-content: space-between; }}
        .signatures {{ margin-top: 40px; display: flex; justify-content: space-between; }}
        .sig-box {{ width: 40%; border-top: 1px solid #0f172a; text-align: center; padding-top: 8px; font-size: 10pt; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{titlu}</h1>
        <p><strong>Instituție:</strong> {institutie} | <strong>Generat la:</strong> {now_str} | <strong>Total înregistrări:</strong> {len(transfers)}</p>
        <p><em>Conform HG 585/2002 privind protecția informațiilor clasificate și HG 1349/2002</em></p>
    </div>

    <table>
        <thead>
            <tr>
                <th>Nr. Registru</th>
                <th>Data / Ora</th>
                <th>Clasificare</th>
                <th>Sursă</th>
                <th>Persoană / Predător</th>
                <th>Mediu Transfer</th>
                <th>Destinație</th>
                <th>Conținut / Hash</th>
                <th>Status & Semnătură</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <div class="signatures">
        <div class="sig-box">
            <strong>Gestionar Registru / Operator</strong><br><br><br>
            Semnătura: ...........................................
        </div>
        <div class="sig-box">
            <strong>Ofițer de Securitate / Verificator</strong><br><br><br>
            Semnătura: ...........................................
        </div>
    </div>

    <div class="footer">
        <span>Document generat prin Registru Transferuri Media v3.0 (Air-Gapped Edition)</span>
        <span>Pagina 1 / 1</span>
    </div>
</body>
</html>

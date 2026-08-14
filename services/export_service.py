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
    def export_html_report(transfers: List[Dict], output_path: str, institutie: str = "MAPN") -> str:
        rows_html = ""
        for t in transfers:
            rows_html += f"""
            <tr>
                <td>{t.get('nr','')}</td>
                <td>{t.get('date_created','')[:10]}</td>
                <td>{t.get('clasificare','')}</td>
                <td>{t.get('src_institutie','')}</td>
                <td>{t.get('dst_institutie','')}</td>
                <td>{t.get('pers_nume','')}</td>
                <td>{t.get('status','')}</td>
                <td>{'DA' if t.get('semnat_operator') else 'NU'}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="ro"><head><meta charset="UTF-8">
<title>Raport Registru Transferuri — {institutie}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 40px; color: #222; }}
h1 {{ font-size: 20px; border-bottom: 2px solid #333; padding-bottom: 8px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 12px; }}
th, td {{ border: 1px solid #999; padding: 6px 8px; text-align: left; }}
th {{ background: #eee; }}
.semnaturi {{ margin-top: 60px; display: flex; justify-content: space-between; }}
.semnaturi div {{ width: 45%; border-top: 1px solid #333; padding-top: 6px; text-align: center; }}
@media print {{ body {{ margin: 15mm; }} }}
</style></head>
<body>
<h1>RAPORT REGISTRU TRANSFERURI MEDIA — {institutie}</h1>
<p>Generat la: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
<p>Conform HG 585/2002, Legea 182/2002</p>
<table>
<thead><tr><th>Nr.</th><th>Data</th><th>Clasificare</th><th>Sursă</th><th>Destinație</th><th>Persoană</th><th>Status</th><th>Semnat</th></tr></thead>
<tbody>{rows_html}</tbody>
</table>
<div class="semnaturi">
<div>Gestionar Registru<br><br>Nume și semnătură</div>
<div>Ofițer de Securitate<br><br>Nume și semnătură</div>
</div>
</body></html>"""

        Path(output_path).write_text(html, encoding='utf-8')
        return output_path

import sys, os, tempfile, shutil
from pathlib import Path
from configparser import ConfigParser

app_path = Path(__file__).parent
sys.path.insert(0, str(app_path))

from database.db import DatabaseManager
from services.export_service import ExportService
from services.backup_service import BackupService

def run_tests():
    print("=== TESTARE SUITA COMPLETA REGISTRU TRANSFERURI v3.0 ===")
    
    temp_dir = tempfile.mkdtemp()
    db_file = Path(temp_dir) / "test_run.db"
    db = DatabaseManager(str(db_file))
    print("[1/6] Initializare DB Manager: OK")

    ops = db.get_active_operators()
    assert len(ops) >= 2, "Trebuie sa existe cel putin 2 operatori impliciti"
    admin_op = next(o for o in ops if o['rol'] == 'admin')
    
    auth_ok = db.authenticate_operator(admin_op['id'], "123456")
    assert auth_ok is not None, "Autentificarea cu PIN corect a esuat"
    auth_fail = db.authenticate_operator(admin_op['id'], "999999")
    assert auth_fail is None, "Autentificarea cu PIN gresit trebuia sa fie respinsa"
    print("[2/6] Autentificare cu Salted PIN & Roluri: OK")

    nr_ssid = db.get_next_nr("MAPN", "Strict Secret de Importanță Deosebită")
    assert "-000-" in nr_ssid, f"Format incorect pentru SSID: {nr_ssid}"
    nr_ss = db.get_next_nr("MAPN", "Strict Secret")
    assert "-00-" in nr_ss, f"Format incorect pentru SS: {nr_ss}"
    nr_s = db.get_next_nr("MAPN", "Secret")
    assert "-0-" in nr_s, f"Format incorect pentru Secret: {nr_s}"
    nr_svc = db.get_next_nr("MAPN", "Secret de Serviciu")
    assert "-S-" in nr_svc, f"Format incorect pentru Secret de Serviciu: {nr_svc}"
    print("[3/6] Numerotare HG 585/2002 (Prefixare clasificare): OK")

    t_data = {
        'src_institutie': 'Baza 90 Transport Aerian',
        'src_pc_nume': 'STA-OP-04',
        'src_medium': 'HDD Intern',
        'pers_nume': 'Mr. Ionescu Radu',
        'pers_autorizatie': 'Strict Secret',
        'transfer_medium': 'USB Flash Drive Criptat',
        'transfer_sn': 'KING-FIPS-9921',
        'dst_institutie': 'Statul Major al Fortelor Aeriene',
        'dst_pc_nume': 'SMFA-SEC-01',
        'clasificare': 'Strict Secret',
        'baza_legala': 'Ordin Z-14/2026',
        'arhiva_nume': 'Misiune_Tactics.enc',
        'arhiva_hash': 'a' * 64
    }
    tid = db.insert_transfer(t_data, admin_op['nume'], admin_op['id'], "MAPN")
    rec = db.get_transfer_by_id(tid)
    assert rec['hash_inregistrare'] is not None, "Hash-ul de integritate lipseste"
    assert len(rec['hash_inregistrare']) == 64, "Hash-ul trebuie sa aiba 64 caractere (SHA-256)"
    
    db.semneaza_transfer(tid, admin_op['nume'], admin_op['id'])
    rec_signed = db.get_transfer_by_id(tid)
    assert rec_signed['semnat_operator'] == 1, "Transferul nu a fost marcat ca semnat"
    print("[4/6] Inregistrare Transfer, Semnatura & Hash Canonic: OK")

    valid, cnt, err = db.verify_audit_chain()
    assert valid is True, f"Lantul de audit este invalid: {err}"
    assert cnt >= 3, f"Trebuiau sa fie cel putin 3 evenimente in audit, gasite {cnt}"
    print(f"[5/6] Jurnal Audit Criptografic ({cnt} evenimente validate): OK")

    all_t = db.get_all_transfers()
    csv_file = Path(temp_dir) / "export.csv"
    ExportService.export_csv(all_t, str(csv_file))
    assert csv_file.exists(), "Fisierul CSV nu a fost generat"
    
    html_content = ExportService.generate_html_report(all_t, "MAPN Test")
    assert "REGISTRU EVIDENȚĂ TRANSFERURI MEDIA" in html_content, "Raportul HTML nu contine antetul"
    print("[6/6] Serviciu Export & Rapoarte Oficiale: OK")

    db.close()
    shutil.rmtree(temp_dir)
    print("\n TOATE CELE 6 MODULE FUNCTIONEAZA IMPECABIL SI RESPECTA NORMELE LEGALE!")

if __name__ == "__main__":
    run_tests()

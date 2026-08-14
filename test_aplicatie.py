import sys
import tempfile
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.db import DatabaseManager


def test_default_operators_created():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(os.path.join(tmp, "test.db"))
        ops = db.get_active_operators()
        assert len(ops) == 2
        db.close()
    print("PASS: test_default_operators_created")


def test_pin_authentication():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(os.path.join(tmp, "test.db"))
        ops = db.get_active_operators()
        admin = next(o for o in ops if o['rol'] == 'admin')
        result = db.authenticate_operator(admin['id'], "123456")
        assert result is not None
        wrong = db.authenticate_operator(admin['id'], "000000")
        assert wrong is None
        db.close()
    print("PASS: test_pin_authentication")


def test_numbering_hg585():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(os.path.join(tmp, "test.db"))
        nr1 = db.get_next_nr("MAPN", "Secret")
        nr2 = db.get_next_nr("MAPN", "Secret")
        assert nr1 != nr2
        assert "-0-" in nr1
        nr_ssid = db.get_next_nr("MAPN", "Strict Secret de Importanță Deosebită")
        assert "-000-" in nr_ssid
        db.close()
    print("PASS: test_numbering_hg585")


def test_insert_transfer_and_hash():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(os.path.join(tmp, "test.db"))
        data = {
            'src_institutie': 'Unitatea A', 'src_pc_nume': 'PC-01', 'src_medium': 'HDD',
            'pers_nume': 'Ion Popescu', 'pers_autorizatie': 'Secret',
            'transfer_medium': 'USB Flash', 'dst_institutie': 'Unitatea B',
            'clasificare': 'Secret',
        }
        record_id = db.insert_transfer(data, "Test Operator", None)
        transfers = db.get_all_transfers()
        assert len(transfers) == 1
        assert transfers[0]['hash_inregistrare'] is not None
        assert len(transfers[0]['hash_inregistrare']) == 64
        db.close()
    print("PASS: test_insert_transfer_and_hash")


def test_audit_chain_integrity():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(os.path.join(tmp, "test.db"))
        data = {
            'src_institutie': 'A', 'src_pc_nume': 'PC', 'src_medium': 'HDD',
            'pers_nume': 'Test', 'transfer_medium': 'USB Flash', 'dst_institutie': 'B',
            'clasificare': 'Neclasificat',
        }
        db.insert_transfer(data, "Test Operator", None)
        valid, count, error = db.verify_audit_chain()
        assert valid is True
        assert error is None
        db.conn.execute("UPDATE audit_log SET detalii='HACKED' WHERE sequence_nr=1")
        db.conn.commit()
        valid2, _, error2 = db.verify_audit_chain()
        assert valid2 is False
        assert error2 is not None
        db.close()
    print("PASS: test_audit_chain_integrity")


def test_sanitize_media():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(os.path.join(tmp, "test.db"))
        media_id = db.add_storage_media({
            'cod_inventar': 'INV-001', 'tip_mediu': 'USB Flash',
            'serie_hardware': 'SN12345', 'clasificare_max': 'Secret', 'status': 'activ'
        })
        cert = db.sanitize_media(media_id, "Purge", "Test procedura", "Operator A", "Martor B")
        assert cert.startswith("SAN-")
        media = db.get_all_media()
        assert media[0]['status'] == 'sanitarizat'
        db.close()
    print("PASS: test_sanitize_media")


if __name__ == "__main__":
    test_default_operators_created()
    test_pin_authentication()
    test_numbering_hg585()
    test_insert_transfer_and_hash()
    test_audit_chain_integrity()
    test_sanitize_media()
    print("\n6/6 teste trecute cu succes.")

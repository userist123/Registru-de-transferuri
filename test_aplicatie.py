import sys
import tempfile
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.db import DatabaseManager


def test_default_operators_and_nato_clearance():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(os.path.join(tmp, "test.db"))
        ops = db.get_active_operators()
        assert len(ops) == 2
        admin = next(o for o in ops if o['rol'] == 'admin')
        assert admin['autorizatie_nato'] == 'COSMIC TOP SECRET'
        db.close()
    print("PASS: test_default_operators_and_nato_clearance")


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
        nr_ssv = db.get_next_nr("MAPN", "Secret de Serviciu")
        assert "-S-" in nr_ssv
        db.close()
    print("PASS: test_numbering_hg585")


def test_endpoint_protector_device_fingerprinting():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(os.path.join(tmp, "test.db"))
        # Enroll device
        dev_id = db.add_amprentat_medium({
            'cod_inventar': 'MAPN-USB-SEC-01',
            'tip_mediu': 'Stick USB',
            'producator': 'SanDisk',
            'model': 'Ultra Flair',
            'vid': '0781',
            'pid': '5583',
            'serie_hardware': '4C53000123456789',
            'capacitate_gb': 64.0,
            'clasificare_max': 'Secret',
            'status_politica': 'autorizat_rw',
            'stare_criptare': 'BitLocker To Go (AES-256)'
        }, "Admin Test")
        
        # Verify lookup by fingerprint
        matched = db.find_medium_by_fingerprint('0781', '5583', '4C53000123456789')
        assert matched is not None
        assert matched['id'] == dev_id
        assert matched['clasificare_max'] == 'Secret'
        assert matched['clasificare_max_nato'] == 'NATO CONFIDENTIAL'
        assert matched['status_politica'] == 'autorizat_rw'
        
        # Test policy update
        db.update_medium_policy(dev_id, 'autorizat_ro', 'Admin Test', 'Test restrictie read-only')
        updated = db.get_medium_by_id(dev_id)
        assert updated['status_politica'] == 'autorizat_ro'
        db.close()
    print("PASS: test_endpoint_protector_device_fingerprinting")


def test_device_classification_ceiling_enforcement():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(os.path.join(tmp, "test.db"))
        # Enroll a device with max classification ceiling 'Secret de Serviciu'
        dev_id = db.add_amprentat_medium({
            'cod_inventar': 'MAPN-USB-SSV',
            'tip_mediu': 'Stick USB',
            'vid': '0951',
            'pid': '1666',
            'serie_hardware': 'SN-SSV-999',
            'clasificare_max': 'Secret de Serviciu',
            'status_politica': 'autorizat_rw'
        }, "Admin Test")

        # 1. Allowed: Transfer with 'Neclasificat' or 'Secret de Serviciu'
        ok, reason = db.is_classification_allowed_on_medium(dev_id, 'Neclasificat')
        assert ok is True
        ok, reason = db.is_classification_allowed_on_medium(dev_id, 'Secret de Serviciu')
        assert ok is True

        # 2. Blocked: Transfer with 'Strict Secret' on a medium allowed only up to 'Secret de Serviciu'
        blocked, reason = db.is_classification_allowed_on_medium(dev_id, 'Strict Secret')
        assert blocked is False
        assert "Violare Plafon de Securitate" in reason

        # 3. Blocked: If policy is changed to 'blocat'
        db.update_medium_policy(dev_id, 'blocat', 'Admin Test', 'Incident securitate')
        blocked_pol, reason_pol = db.is_classification_allowed_on_medium(dev_id, 'Neclasificat')
        assert blocked_pol is False
        assert "BLOCAT" in reason_pol

        db.close()
    print("PASS: test_device_classification_ceiling_enforcement")


def test_insert_transfer_with_nato_eu_and_hash():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(os.path.join(tmp, "test.db"))
        dev_id = db.add_amprentat_medium({
            'cod_inventar': 'MED-001',
            'vid': '0781', 'pid': '5583', 'serie_hardware': 'SN-SEC-01',
            'clasificare_max': 'Strict Secret'
        }, "Admin Test")

        data = {
            'directie_transfer': 'iesire',
            'src_institutie': 'MApN / U.M. 01234',
            'src_pc_nume': 'PC-01',
            'src_medium': 'SSD Extern',
            'pers_nume': 'Lt. Col. Marinescu',
            'pers_autorizatie': 'Strict Secret',
            'curier_militar_nume': 'Sgt. Ionescu',
            'curier_militar_legitimatie': 'CUR-9988',
            'transfer_medium': 'SSD Extern',
            'transfer_sn': 'SN-SEC-01',
            'transfer_vid': '0781',
            'transfer_pid': '5583',
            'storage_medium_id': dev_id,
            'dst_institutie': 'Statul Major al Apărării',
            'arhiva_nume': 'Harta_Tactice_2026.7z',
            'arhiva_tip': '7Z Criptat AES-256',
            'arhiva_hash': 'A1B2C3D4E5F60718293A4B5C6D7E8F90A1B2C3D4E5F60718293A4B5C6D7E8F90',
            'clasificare': 'Strict Secret',
            'scanat_antivirus': 1
        }
        record_id = db.insert_transfer(data, "Operator Test", None)
        transfers = db.get_all_transfers()
        assert len(transfers) == 1
        tx = transfers[0]
        assert tx['clasificare'] == 'Strict Secret'
        assert tx['clasificare_nato'] == 'NATO SECRET'
        assert tx['clasificare_eu'] == 'SECRET UE / EU SECRET'
        assert tx['directie_transfer'] == 'iesire'
        assert tx['hash_inregistrare'] is not None
        assert len(tx['hash_inregistrare']) == 64
        db.close()
    print("PASS: test_insert_transfer_with_nato_eu_and_hash")


def test_four_eyes_approval():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(os.path.join(tmp, "test.db"))
        data = {
            'src_institutie': 'A', 'src_pc_nume': 'PC1', 'src_medium': 'USB',
            'pers_nume': 'Pers1', 'transfer_medium': 'USB', 'dst_institutie': 'B',
            'arhiva_nume': 'Docs.zip', 'arhiva_hash': 'E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855',
            'clasificare': 'Secret'
        }
        tid = db.insert_transfer(data, "Op1", None)
        res = db.approve_four_eyes(tid, "Cpt. Aprobator", "Ofițer Securitate", "op-id-1")
        assert res is True
        tx = db.get_all_transfers()[0]
        assert tx['four_eyes_aprobator'] == 'Cpt. Aprobator'
        assert tx['four_eyes_functie'] == 'Ofițer Securitate'
        assert tx['four_eyes_aprobat_la'] is not None
        db.close()
    print("PASS: test_four_eyes_approval")


def test_audit_chain_tamper_detection():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(os.path.join(tmp, "test.db"))
        data = {
            'src_institutie': 'A', 'src_pc_nume': 'PC', 'src_medium': 'USB',
            'pers_nume': 'Test', 'transfer_medium': 'USB Flash', 'dst_institutie': 'B',
            'arhiva_nume': 'file.zip', 'arhiva_hash': 'E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855',
            'clasificare': 'Neclasificat'
        }
        db.insert_transfer(data, "Test Operator", None)
        valid, count, error = db.verify_audit_chain()
        assert valid is True
        assert count >= 1
        assert error is None
        
        # Tamper simulation
        db.conn.execute("UPDATE audit_log SET detalii='HACKED' WHERE sequence_nr=1")
        db.conn.commit()
        valid2, _, error2 = db.verify_audit_chain()
        assert valid2 is False
        assert error2 is not None
        db.close()
    print("PASS: test_audit_chain_tamper_detection")


def test_sanitize_media_nist80088r2():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(os.path.join(tmp, "test.db"))
        media_id = db.add_amprentat_medium({
            'cod_inventar': 'MED-SAN-01', 'tip_mediu': 'SSD Extern',
            'vid': '0781', 'pid': '5583',
            'serie_hardware': 'SN-SAN-999', 'clasificare_max': 'Secret', 'status_politica': 'autorizat_rw'
        }, "Admin Test")
        cert = db.sanitize_media(media_id, "Purge", "Suprascriere Crypto-Erase conform NIST SP 800-88r2", "Operator A", "Martor B")
        assert cert.startswith("SAN-NIST88-")
        media = db.get_medium_by_id(media_id)
        assert media['status_politica'] == 'autorizat_rw' # Purge allows reuse
        
        # Destroy test
        cert_destroy = db.sanitize_media(media_id, "Destroy", "Dezintegrare fizica DIN 66399 H-5", "Operator A", "Martor B")
        media_destroyed = db.get_medium_by_id(media_id)
        assert media_destroyed['status_politica'] == 'blocat'
        db.close()
    print("PASS: test_sanitize_media_nist80088r2")


if __name__ == "__main__":
    test_default_operators_and_nato_clearance()
    test_pin_authentication()
    test_numbering_hg585()
    test_endpoint_protector_device_fingerprinting()
    test_device_classification_ceiling_enforcement()
    test_insert_transfer_with_nato_eu_and_hash()
    test_four_eyes_approval()
    test_audit_chain_tamper_detection()
    test_sanitize_media_nist80088r2()
    print("\n9/9 teste trecute cu succes.")

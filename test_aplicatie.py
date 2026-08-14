#!/usr/bin/env python3
"""Test automatizat pentru aplicație"""
import sys
from pathlib import Path

print("========================================")
print("  TEST AUTOMATIZAT APLICAȚIE")
print("========================================\n")

# Test 1: Import module
print("[1/4] Test importuri...")
try:
    from database.db import DatabaseManager
    from ui.main_window import MainWindow
    print("✓ Toate modulele importate cu succes\n")
except Exception as e:
    print(f"✗ Eroare import: {e}\n")
    sys.exit(1)

# Test 2: Bază de date
print("[2/4] Test bază de date...")
try:
    db = DatabaseManager("test_aplicatie.db")
    stats = db.get_stats()
    print(f"✓ Bază de date funcțională: {stats['total']} înregistrări\n")
except Exception as e:
    print(f"✗ Eroare DB: {e}\n")
    sys.exit(1)

# Test 3: Operații CRUD
print("[3/4] Test inserare date...")
try:
    data = {
        "src_institutie": "Test Unit",
        "src_pc_nume": "PC-TEST-001",
        "src_medium": "USB Flash Drive",
        "pers_nume": "Test Operator",
        "transfer_medium": "HDD Extern",
        "dst_institutie": "Destinație Test",
        "clasificare": "Nesecret"
    }
    tid = db.insert_transfer(data, "Admin Test")
    print(f"✓ Transfer creat: {tid[:8]}...\n")
except Exception as e:
    print(f"✗ Eroare inserare: {e}\n")
    sys.exit(1)

# Test 4: Citire date
print("[4/4] Test citire date...")
try:
    transfers = db.get_all_transfers()
    print(f"✓ Citire reușită: {len(transfers)} transferuri\n")
    db.close()
    Path("test_aplicatie.db").unlink(missing_ok=True)
    Path("test_aplicatie.db-shm").unlink(missing_ok=True)
    Path("test_aplicatie.db-wal").unlink(missing_ok=True)
except Exception as e:
    print(f"✗ Eroare citire: {e}\n")
    sys.exit(1)

print("========================================")
print("✅ TOATE TESTELE AU TRECUT!")
print("========================================\n")
print("Aplicația este funcțională și poate fi pornită cu:")
print("  python3 main.py\n")

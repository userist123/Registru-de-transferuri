"""Migrare transferuri.db v3.0 (SQLite plaintext) -> v3.1 (pregatire import SQLCipher).
Ruleaza in Python inainte de prima pornire a aplicatiei C#.
"""
import sqlite3, hashlib, json, sys

def canonical_hash(rec):
    sep = "\u001f"
    fields = [rec["registry_number"], str(rec["classification"]), rec["transfer_date_utc"],
              rec["source_institution"].strip(), rec["destination_institution"].strip(),
              rec["source_person"].strip(), rec["destination_person"].strip(),
              rec["media_type"].strip(), rec["media_serial"].strip(),
              rec.get("media_inventory_code","").strip(), rec.get("content_description","").strip(),
              rec["operator_username"].strip()]
    return hashlib.sha256(sep.join(fields).encode("utf-8")).hexdigest().upper()

def migrate(src_path, out_json):
    conn = sqlite3.connect(src_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM transfers").fetchall()
    out = []
    for r in rows:
        rec = dict(r)
        rec["integrity_hash_v31"] = canonical_hash(rec)
        out.append(rec)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print(f"Migrat {len(out)} inregistrari -> {out_json}")

if __name__ == "__main__":
    migrate(sys.argv[1] if len(sys.argv) > 1 else "transferuri.db", "migrare_v31.json")

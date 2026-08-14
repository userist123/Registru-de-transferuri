import sqlite3, hashlib, json, uuid, logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict

class DatabaseManager:
    def __init__(self, db_path: str = "transferuri.db"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()
    
    def _init_schema(self):
        schema_file = Path(__file__).parent / "schema.sql"
        if schema_file.exists():
            self.conn.executescript(schema_file.read_text())
            self.conn.commit()
    
    def get_next_nr(self, prefix: str = "REG") -> str:
        an = datetime.now().year
        cursor = self.conn.execute(
            "INSERT INTO contoare(an, contor) VALUES(?, 1) "
            "ON CONFLICT(an) DO UPDATE SET contor=contor+1 RETURNING contor", (an,)
        )
        contor = cursor.fetchone()[0]
        self.conn.commit()
        return f"{prefix}-{an}-{contor:04d}"
    
    def _hash_record(self, data: dict) -> str:
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def insert_transfer(self, data: dict, operator: str) -> str:
        record_id = str(uuid.uuid4())
        nr = data.get('nr') or self.get_next_nr()
        now = datetime.now().isoformat()
        fields = {**data, "id": record_id, "nr": nr, "date_created": now,
                  "date_modified": now, "operator": operator,
                  "hash_inregistrare": self._hash_record({"nr": nr, "src_institutie": data.get("src_institutie")})}
        cols = ", ".join(fields.keys())
        self.conn.execute(f"INSERT INTO transferuri ({cols}) VALUES ({','.join(['?']*len(fields))})", list(fields.values()))
        self.conn.commit()
        self._log_audit(record_id, "CREATE", operator, f"Creat {nr}")
        self._update_autocomplete(data)
        return record_id
    
    def get_all_transfers(self, filters: dict = None) -> List[Dict]:
        query = "SELECT * FROM transferuri WHERE status != 'anulat'"
        params = []
        if filters and filters.get("text"):
            q = f"%{filters['text']}%"
            query += " AND (src_institutie LIKE ? OR pers_nume LIKE ?)"
            params.extend([q, q])
        query += " ORDER BY date_created DESC"
        return [dict(r) for r in self.conn.execute(query, params).fetchall()]
    
    def _update_autocomplete(self, data: dict):
        now = datetime.now().isoformat()
        for cat, key in [("institutie", "src_institutie"), ("persoana", "pers_nume")]:
            if data.get(key):
                self.conn.execute(
                    "INSERT INTO autocomplete VALUES(?,?,1,?) ON CONFLICT DO UPDATE SET frecventa=frecventa+1",
                    (cat, data[key], now)
                )
        self.conn.commit()
    
    def get_autocomplete(self, cat: str) -> List[str]:
        return [r[0] for r in self.conn.execute(
            "SELECT valoare FROM autocomplete WHERE categorie=? ORDER BY frecventa DESC LIMIT 20", (cat,)
        ).fetchall()]
    
    def _log_audit(self, tid: str, act: str, op: str, det: str = ""):
        self.conn.execute("INSERT INTO audit_log VALUES(?,?,?,?,?,?)",
                         (str(uuid.uuid4()), tid, act, op, datetime.now().isoformat(), det))
        self.conn.commit()
    
    def get_stats(self) -> dict:
        total = self.conn.execute("SELECT COUNT(*) FROM transferuri WHERE status != 'anulat'").fetchone()[0]
        clf = self.conn.execute("SELECT clasificare, COUNT(*) FROM transferuri WHERE status != 'anulat' GROUP BY clasificare").fetchall()
        return {"total": total, "by_clasificare": {r[0]: r[1] for r in clf}}
    
    def close(self):
        self.conn.close()

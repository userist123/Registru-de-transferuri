import sqlite3, hashlib, json, uuid, logging, secrets
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

class DatabaseManager:
    PREFIX_MAP = {
        'Strict Secret de Importanta Deosebita': '000',
        'Strict Secret de Importanță Deosebită': '000',
        'Strict Secret': '00',
        'Secret': '0',
        'Secret de Serviciu': 'S',
        'Neclasificat': 'NC'
    }

    def __init__(self, db_path: str = "transferuri.db"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()
        self._ensure_default_operators()

    def _init_schema(self):
        schema_file = Path(__file__).parent / "schema.sql"
        if schema_file.exists():
            self.conn.executescript(schema_file.read_text(encoding='utf-8'))
            self.conn.commit()

    @staticmethod
    def hash_pin(pin: str, salt: Optional[str] = None) -> Tuple[str, str]:
        if not salt:
            salt = secrets.token_hex(16)
        hashed = hashlib.sha256(f"{salt}{pin}".encode('utf-8')).hexdigest()
        return hashed, salt

    @staticmethod
    def verify_pin(pin: str, stored_hash: str, salt: str) -> bool:
        test_hash, _ = DatabaseManager.hash_pin(pin, salt)
        return test_hash == stored_hash

    def _ensure_default_operators(self):
        cur = self.conn.execute("SELECT COUNT(*) FROM operatori")
        if cur.fetchone()[0] == 0:
            now = datetime.now().isoformat()
            h_admin, s_admin = self.hash_pin("123456")
            self.conn.execute(
                "INSERT INTO operatori (id, nume, functie, autorizatie, rol, pin_hash, salt, activ, date_created, date_modified) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
                (str(uuid.uuid4()), "Administrator Sistem", "Ofițer Securitate IT", "Strict Secret de Importanță Deosebită", "admin", h_admin, s_admin, now, now)
            )
            h_op, s_op = self.hash_pin("111111")
            self.conn.execute(
                "INSERT INTO operatori (id, nume, functie, autorizatie, rol, pin_hash, salt, activ, date_created, date_modified) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
                (str(uuid.uuid4()), "Operator Registru", "Operator Transfer Media", "Secret", "operator", h_op, s_op, now, now)
            )
            self.conn.commit()

    def get_active_operators(self) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT id, nume, functie, autorizatie, rol FROM operatori WHERE activ=1 ORDER BY nume ASC"
        ).fetchall()
        return [dict(r) for r in rows]

    def authenticate_operator(self, operator_id: str, pin: str) -> Optional[Dict]:
        row = self.conn.execute(
            "SELECT * FROM operatori WHERE id=? AND activ=1", (operator_id,)
        ).fetchone()
        if not row:
            return None
        if self.verify_pin(pin, row['pin_hash'], row['salt']):
            now = datetime.now().isoformat()
            self.conn.execute("UPDATE operatori SET last_login=? WHERE id=?", (now, operator_id))
            self.conn.commit()
            self._log_audit(None, "LOGIN", row['nume'], f"Autentificare reusita pentru {row['nume']}", op_id=operator_id)
            return dict(row)
        else:
            self._log_audit(None, "LOGIN_FAILED", row['nume'], f"Incercare esuata PIN pentru {row['nume']}", op_id=operator_id)
            return None

    def add_operator(self, nume: str, functie: str, autorizatie: str, rol: str, pin: str, creator: str) -> str:
        op_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        p_hash, salt = self.hash_pin(pin)
        self.conn.execute(
            "INSERT INTO operatori (id, nume, functie, autorizatie, rol, pin_hash, salt, activ, date_created, date_modified) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
            (op_id, nume, functie, autorizatie, rol, p_hash, salt, now, now)
        )
        self.conn.commit()
        self._log_audit(None, "CREATE_OPERATOR", creator, f"Adaugat operator {nume} ({rol}, {autorizatie})")
        return op_id

    def get_next_nr(self, prefix_institutie: str = "MAPN", clasificare: str = "Neclasificat") -> str:
        an = datetime.now().year
        prefix_sec = self.PREFIX_MAP.get(clasificare, 'NC')
        
        cursor = self.conn.execute(
            "INSERT INTO contoare(an, clasificare, contor) VALUES(?, ?, 1) "
            "ON CONFLICT(an, clasificare) DO UPDATE SET contor=contor+1 RETURNING contor",
            (an, clasificare)
        )
        contor = cursor.fetchone()[0]
        self.conn.commit()
        
        return f"{prefix_institutie}-{an}-{prefix_sec}-{contor:04d}"

    def calculate_record_hash(self, data: dict) -> str:
        exclude = {'id', 'hash_inregistrare', 'date_modified', 'semnat_operator', 'semnat_de', 'semnat_la'}
        canonical_dict = {k: str(v) for k, v in data.items() if k not in exclude and v is not None}
        canonical_json = json.dumps(canonical_dict, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

    def _log_audit(self, transfer_id: Optional[str], actiune: str, operator: str, detalii: str = "", op_id: Optional[str] = None):
        last_entry = self.conn.execute("SELECT sequence_nr, entry_hash FROM audit_log ORDER BY sequence_nr DESC LIMIT 1").fetchone()
        
        if last_entry:
            seq_nr = last_entry['sequence_nr'] + 1
            prev_hash = last_entry['entry_hash']
        else:
            seq_nr = 1
            prev_hash = "GENESIS_HASH_00000000000000000000000000000000000000000000000000000000"

        now = datetime.now().isoformat()
        entry_id = str(uuid.uuid4())
        
        payload = f"{prev_hash}|{seq_nr}|{now}|{actiune}|{operator}|{transfer_id or ''}|{detalii}"
        entry_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        
        self.conn.execute(
            "INSERT INTO audit_log (id, sequence_nr, transfer_id, actiune, operator, operator_id, timestamp, detalii, previous_hash, entry_hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (entry_id, seq_nr, transfer_id, actiune, operator, op_id, now, detalii, prev_hash, entry_hash)
        )
        self.conn.commit()

    def verify_audit_chain(self) -> Tuple[bool, int, Optional[str]]:
        entries = self.conn.execute("SELECT * FROM audit_log ORDER BY sequence_nr ASC").fetchall()
        if not entries:
            return True, 0, None
        
        expected_prev = "GENESIS_HASH_00000000000000000000000000000000000000000000000000000000"
        for row in entries:
            if row['previous_hash'] != expected_prev:
                return False, row['sequence_nr'], f"Lant corupt la evenimentul #{row['sequence_nr']}: previous_hash invalid"
            
            payload = f"{expected_prev}|{row['sequence_nr']}|{row['timestamp']}|{row['actiune']}|{row['operator']}|{row['transfer_id'] or ''}|{row['detalii'] or ''}"
            computed_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
            if computed_hash != row['entry_hash']:
                return False, row['sequence_nr'], f"Lant alterat la evenimentul #{row['sequence_nr']}: entry_hash nu corespunde"
            
            expected_prev = row['entry_hash']
            
        return True, len(entries), None

    def insert_transfer(self, data: dict, operator: str, operator_id: Optional[str] = None, prefix_institutie: str = "MAPN") -> str:
        record_id = str(uuid.uuid4())
        clasificare = data.get('clasificare', 'Neclasificat')
        nr = data.get('nr') or self.get_next_nr(prefix_institutie, clasificare)
        now = datetime.now().isoformat()
        
        data_to_insert = {**data, 'id': record_id, 'nr': nr, 'date_created': now, 'date_modified': now, 'operator': operator, 'operator_id': operator_id}
        
        record_hash = self.calculate_record_hash(data_to_insert)
        data_to_insert['hash_inregistrare'] = record_hash
        
        cols = ", ".join(data_to_insert.keys())
        placeholders = ", ".join(["?"] * len(data_to_insert))
        self.conn.execute(f"INSERT INTO transferuri ({cols}) VALUES ({placeholders})", list(data_to_insert.values()))
        self.conn.commit()
        
        self._log_audit(record_id, "CREATE_TRANSFER", operator, f"Inregistrat transfer {nr} [{clasificare}] de la {data.get('src_institutie')} la {data.get('dst_institutie')}", op_id=operator_id)
        self._update_autocomplete(data)
        return record_id

    def semneaza_transfer(self, transfer_id: str, operator_name: str, operator_id: str) -> bool:
        row = self.conn.execute("SELECT * FROM transferuri WHERE id=?", (transfer_id,)).fetchone()
        if not row:
            return False
        if row['semnat_operator'] == 1:
            return True
        
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE transferuri SET semnat_operator=1, semnat_de=?, semnat_la=?, date_modified=? WHERE id=?",
            (operator_name, now, now, transfer_id)
        )
        self.conn.commit()
        self._log_audit(transfer_id, "SIGN_TRANSFER", operator_name, f"Semnat formal transfer {row['nr']} de catre {operator_name}", op_id=operator_id)
        return True

    def anuleaza_transfer(self, transfer_id: str, motiv: str, operator_name: str, operator_id: str) -> bool:
        row = self.conn.execute("SELECT * FROM transferuri WHERE id=?", (transfer_id,)).fetchone()
        if not row:
            return False
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE transferuri SET status='anulat', motiv_anulare=?, date_modified=? WHERE id=?",
            (motiv, now, transfer_id)
        )
        self.conn.commit()
        self._log_audit(transfer_id, "CANCEL_TRANSFER", operator_name, f"Anulat transfer {row['nr']}. Motiv: {motiv}", op_id=operator_id)
        return True

    def get_all_transfers(self, filters: Optional[dict] = None) -> List[Dict]:
        query = "SELECT * FROM transferuri WHERE 1=1"
        params = []
        
        if filters:
            if filters.get("status"):
                query += " AND status = ?"
                params.append(filters["status"])
            if filters.get("text"):
                q = f"%{filters['text']}%"
                query += " AND (src_institutie LIKE ? OR pers_nume LIKE ? OR nr LIKE ? OR dst_institutie LIKE ? OR arhiva_nume LIKE ? OR transfer_sn LIKE ?)"
                params.extend([q, q, q, q, q, q])
            if filters.get("clasificare") and filters["clasificare"] != "Toate":
                query += " AND clasificare = ?"
                params.append(filters["clasificare"])
            if filters.get("data_start"):
                query += " AND date_created >= ?"
                params.append(filters["data_start"])
            if filters.get("data_end"):
                query += " AND date_created <= ?"
                params.append(filters["data_end"])
            if filters.get("semnat") is not None:
                query += " AND semnat_operator = ?"
                params.append(1 if filters["semnat"] else 0)
                
        query += " ORDER BY date_created DESC"
        return [dict(r) for r in self.conn.execute(query, params).fetchall()]

    def get_transfer_by_id(self, transfer_id: str) -> Optional[Dict]:
        row = self.conn.execute("SELECT * FROM transferuri WHERE id=?", (transfer_id,)).fetchone()
        return dict(row) if row else None

    def add_storage_medium(self, data: dict, operator: str) -> str:
        med_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        fields = {**data, 'id': med_id, 'data_inregistrare': now, 'data_modificare': now}
        cols = ", ".join(fields.keys())
        placeholders = ", ".join(["?"] * len(fields))
        self.conn.execute(f"INSERT INTO medii_stocare ({cols}) VALUES ({placeholders})", list(fields.values()))
        self.conn.commit()
        self._log_audit(None, "REGISTER_MEDIUM", operator, f"Inregistrat suport {data.get('cod_inventar')} ({data.get('tip_mediu')}, S/N: {data.get('serie_hardware')})")
        return med_id

    def get_all_media(self, status: Optional[str] = None) -> List[Dict]:
        if status:
            rows = self.conn.execute("SELECT * FROM medii_stocare WHERE status=? ORDER BY cod_inventar ASC", (status,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM medii_stocare ORDER BY cod_inventar ASC").fetchall()
        return [dict(r) for r in rows]

    def sanitize_medium(self, mediu_id: str, metoda: str, procedura: str, executant: str, martor: str, aprobat: str) -> str:
        med = self.conn.execute("SELECT * FROM medii_stocare WHERE id=?", (mediu_id,)).fetchone()
        if not med:
            raise ValueError("Mediul nu exista.")
        
        cert_id = str(uuid.uuid4())
        cert_nr = f"CERT-SAN-{datetime.now().year}-{secrets.randbelow(9000)+1000}"
        now = datetime.now().isoformat()
        
        self.conn.execute(
            "INSERT INTO jurnal_sanitarizare (id, mediu_id, serie_hardware, metoda, procedura_detalii, operator_executant, martor_verificator, aprobat_de, data_executie, certificat_nr) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cert_id, mediu_id, med['serie_hardware'], metoda, procedura, executant, martor, aprobat, now, cert_nr)
        )
        
        new_status = 'distrus' if metoda.lower() == 'destroy' else 'sanitarizat'
        self.conn.execute("UPDATE medii_stocare SET status=?, data_modificare=? WHERE id=?", (new_status, now, mediu_id))
        self.conn.commit()
        
        self._log_audit(None, "SANITIZE_MEDIUM", executant, f"Sanitarizare {med['cod_inventar']} [{metoda}]. Certificat: {cert_nr}. Martor: {martor}")
        return cert_nr

    def _update_autocomplete(self, data: dict):
        now = datetime.now().isoformat()
        mapping = [
            ("institutie", "src_institutie"), ("institutie", "dst_institutie"),
            ("persoana", "pers_nume"), ("pc", "src_pc_nume"), ("pc", "dst_pc_nume")
        ]
        for cat, key in mapping:
            val = data.get(key)
            if val and str(val).strip():
                self.conn.execute(
                    "INSERT INTO autocomplete (categorie, valoare, frecventa, ultima_data) "
                    "VALUES (?, ?, 1, ?) ON CONFLICT(categorie, valoare) DO UPDATE SET frecventa=frecventa+1, ultima_data=?",
                    (cat, str(val).strip(), now, now)
                )
        self.conn.commit()

    def get_autocomplete(self, cat: str) -> List[str]:
        rows = self.conn.execute(
            "SELECT valoare FROM autocomplete WHERE categorie=? ORDER BY frecventa DESC LIMIT 30", (cat,)
        ).fetchall()
        return [r[0] for r in rows]

    def get_stats(self) -> dict:
        total = self.conn.execute("SELECT COUNT(*) FROM transferuri WHERE status != 'anulat'").fetchone()[0]
        anulate = self.conn.execute("SELECT COUNT(*) FROM transferuri WHERE status = 'anulat'").fetchone()[0]
        semnate = self.conn.execute("SELECT COUNT(*) FROM transferuri WHERE semnat_operator = 1 AND status != 'anulat'").fetchone()[0]
        
        clf_rows = self.conn.execute(
            "SELECT clasificare, COUNT(*) FROM transferuri WHERE status != 'anulat' GROUP BY clasificare"
        ).fetchall()
        
        media_count = self.conn.execute("SELECT COUNT(*) FROM medii_stocare").fetchone()[0]
        media_active = self.conn.execute("SELECT COUNT(*) FROM medii_stocare WHERE status='activ'").fetchone()[0]
        
        audit_count = self.conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        
        return {
            "total": total,
            "anulate": anulate,
            "semnate": semnate,
            "by_clasificare": {r[0]: r[1] for r in clf_rows},
            "media_total": media_count,
            "media_active": media_active,
            "audit_events": audit_count
        }

    def close(self):
        self.conn.close()

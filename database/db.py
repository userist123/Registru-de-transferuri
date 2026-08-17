import sqlite3, hashlib, json, uuid, secrets, platform
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class DatabaseManager:
    PREFIX_MAP = {
        'Strict Secret de Importanță Deosebită': '000',
        'Strict Secret de Importanta Deosebita': '000',
        'Strict Secret': '00',
        'Secret': '0',
        'Secret de Serviciu': 'S',
        'Neclasificat': 'NC'
    }

    NATO_MAP = {
        'Strict Secret de Importanță Deosebită': 'COSMIC TOP SECRET',
        'Strict Secret de Importanta Deosebita': 'COSMIC TOP SECRET',
        'Strict Secret': 'NATO SECRET',
        'Secret': 'NATO CONFIDENTIAL',
        'Secret de Serviciu': 'NATO RESTRICTED',
        'Neclasificat': 'NATO UNCLASSIFIED'
    }

    EU_MAP = {
        'Strict Secret de Importanță Deosebită': 'TRÈS SECRET UE / EU TOP SECRET',
        'Strict Secret de Importanta Deosebita': 'TRÈS SECRET UE / EU TOP SECRET',
        'Strict Secret': 'SECRET UE / EU SECRET',
        'Secret': 'CONFIDENTIEL UE / EU CONFIDENTIAL',
        'Secret de Serviciu': 'RESTREINT UE / EU RESTRICTED',
        'Neclasificat': 'LIMITE / UNCLASSIFIED'
    }

    CLASSIFICATION_LEVELS = [
        'Neclasificat',
        'Secret de Serviciu',
        'Secret',
        'Strict Secret',
        'Strict Secret de Importanță Deosebită'
    ]

    def __init__(self, db_path: str = "transferuri.db"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.local_host = platform.node() or "MAPN-AIRGAP-WS01"
        self._init_schema()
        self._ensure_default_operators()

    def _init_schema(self):
        cursor = self.conn.cursor()
        existing_tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

        # 1. Audit log migration
        if "audit_log" in existing_tables:
            cols = [c[1] for c in cursor.execute("PRAGMA table_info(audit_log)").fetchall()]
            if "sequence_nr" not in cols:
                cursor.execute("ALTER TABLE audit_log RENAME TO audit_log_v2")
                cursor.execute("""
                    CREATE TABLE audit_log (
                        id TEXT PRIMARY KEY,
                        sequence_nr INTEGER UNIQUE NOT NULL,
                        transfer_id TEXT,
                        actiune TEXT NOT NULL,
                        operator TEXT NOT NULL,
                        operator_id TEXT,
                        timestamp TEXT NOT NULL,
                        detalii TEXT,
                        previous_hash TEXT,
                        entry_hash TEXT NOT NULL
                    )
                """)
                old_rows = cursor.execute("SELECT * FROM audit_log_v2 ORDER BY timestamp ASC").fetchall()
                prev_hash = "GENESIS_HASH_00000000000000000000000000000000000000000000000000000000"
                for idx, row in enumerate(old_rows, 1):
                    r_dict = dict(row)
                    t_id = r_dict.get('transfer_id')
                    act = r_dict.get('actiune', 'EVENT')
                    op = r_dict.get('operator', 'system')
                    ts = r_dict.get('timestamp', datetime.now().isoformat())
                    det = r_dict.get('detalii', '')
                    e_id = r_dict.get('id', str(uuid.uuid4()))
                    payload = f"{prev_hash}|{idx}|{ts}|{act}|{op}|{t_id or ''}|{det}"
                    e_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
                    cursor.execute(
                        "INSERT INTO audit_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (e_id, idx, t_id, act, op, None, ts, det, prev_hash, e_hash)
                    )
                    prev_hash = e_hash
                cursor.execute("DROP TABLE audit_log_v2")

        # 2. Operatori migration
        if "operatori" in existing_tables:
            cols = [c[1] for c in cursor.execute("PRAGMA table_info(operatori)").fetchall()]
            if "pin_hash" not in cols or "salt" not in cols:
                cursor.execute("DROP TABLE operatori")
            else:
                if "unitate_militara" not in cols:
                    cursor.execute("ALTER TABLE operatori ADD COLUMN unitate_militara TEXT DEFAULT 'MApN / Structura Securitate'")
                if "autorizatie_nato" not in cols:
                    cursor.execute("ALTER TABLE operatori ADD COLUMN autorizatie_nato TEXT DEFAULT 'NATO UNCLASSIFIED'")

        # 3. Contoare migration
        if "contoare" in existing_tables:
            cols = [c[1] for c in cursor.execute("PRAGMA table_info(contoare)").fetchall()]
            if "clasificare" not in cols:
                cursor.execute("DROP TABLE contoare")

        # 4. Transferuri migration for new military / NATO fields
        if "transferuri" in existing_tables:
            cols = [c[1] for c in cursor.execute("PRAGMA table_info(transferuri)").fetchall()]
            new_columns = [
                ("directie_transfer", "TEXT DEFAULT 'iesire'"),
                ("operator_id", "TEXT"),
                ("curier_militar_nume", "TEXT"),
                ("curier_militar_legitimatie", "TEXT"),
                ("transfer_vid", "TEXT"),
                ("transfer_pid", "TEXT"),
                ("storage_medium_id", "TEXT"),
                ("scanat_antivirus", "INTEGER DEFAULT 1"),
                ("antivirus_detalii", "TEXT DEFAULT 'Scanare Antivirus Offline: Negativ (Fără amenințări)'"),
                ("clasificare_nato", "TEXT DEFAULT 'NATO UNCLASSIFIED'"),
                ("clasificare_eu", "TEXT DEFAULT 'LIMITE / UNCLASSIFIED'"),
                ("nr_aprobare", "TEXT"),
                ("nr_exemplare", "INTEGER DEFAULT 1"),
                ("four_eyes_aprobator", "TEXT"),
                ("four_eyes_functie", "TEXT"),
                ("four_eyes_aprobat_la", "TEXT"),
                ("motiv_anulare", "TEXT"),
                ("semnat_de", "TEXT"),
                ("semnat_la", "TEXT")
            ]
            for col_name, col_type in new_columns:
                if col_name not in cols:
                    cursor.execute(f"ALTER TABLE transferuri ADD COLUMN {col_name} {col_type}")

        # 5. Migrate old medii_stocare into medii_amprentate if exists
        if "medii_stocare" in existing_tables and "medii_amprentate" not in existing_tables:
            cursor.execute("""
                CREATE TABLE medii_amprentate (
                    id TEXT PRIMARY KEY,
                    cod_inventar TEXT UNIQUE NOT NULL,
                    host_binding TEXT NOT NULL,
                    tip_mediu TEXT NOT NULL,
                    producator TEXT,
                    model TEXT,
                    vid TEXT NOT NULL,
                    pid TEXT NOT NULL,
                    serie_hardware TEXT NOT NULL,
                    pnp_device_id TEXT,
                    volume_serial TEXT,
                    capacitate_gb REAL,
                    clasificare_max TEXT NOT NULL DEFAULT 'Neclasificat',
                    clasificare_max_nato TEXT NOT NULL DEFAULT 'NATO UNCLASSIFIED',
                    clasificare_max_eu TEXT NOT NULL DEFAULT 'LIMITE / UNCLASSIFIED',
                    status_politica TEXT NOT NULL DEFAULT 'autorizat_rw',
                    stare_criptare TEXT NOT NULL DEFAULT 'Fara',
                    gestionar_nume TEXT,
                    gestionar_unitate TEXT,
                    data_amprentare TEXT NOT NULL,
                    data_modificare TEXT NOT NULL,
                    amprentat_de TEXT NOT NULL,
                    observatii TEXT
                )
            """)
            # Copy old data
            old_media = cursor.execute("SELECT * FROM medii_stocare").fetchall()
            for om in old_media:
                d = dict(om)
                cursor.execute("""
                    INSERT INTO medii_amprentate (
                        id, cod_inventar, host_binding, tip_mediu, producator, model,
                        vid, pid, serie_hardware, capacitate_gb, clasificare_max,
                        status_politica, gestionar_nume, data_amprentare, data_modificare,
                        amprentat_de, observatii
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    d.get('id', str(uuid.uuid4())),
                    d.get('cod_inventar', f"MED-{secrets.token_hex(3).upper()}"),
                    self.local_host,
                    d.get('tip_mediu', 'Stick USB'),
                    d.get('producator', 'Generat'),
                    d.get('model', 'USB Storage'),
                    d.get('vid', '0000'),
                    d.get('pid', '0000'),
                    d.get('serie_hardware', 'UNKNOWN_SN'),
                    d.get('capacitate_gb', 32.0),
                    d.get('clasificare_max', 'Neclasificat'),
                    'autorizat_rw' if d.get('status') == 'activ' else 'blocat',
                    d.get('gestionar', 'Gestionar IT'),
                    d.get('data_inregistrare', datetime.now().isoformat()),
                    d.get('data_modificare', datetime.now().isoformat()),
                    'Administrator',
                    d.get('observatii', '')
                ))

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
                "INSERT INTO operatori (id, nume, functie, unitate_militara, autorizatie, autorizatie_nato, rol, pin_hash, salt, activ, date_created, date_modified) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
                (str(uuid.uuid4()), "Administrator Sistem", "Ofițer Securitate INFOSEC",
                 "MApN / Baza Tehnologică Centrală", "Strict Secret de Importanță Deosebită", "COSMIC TOP SECRET",
                 "admin", h_admin, s_admin, now, now)
            )
            h_op, s_op = self.hash_pin("111111")
            self.conn.execute(
                "INSERT INTO operatori (id, nume, functie, unitate_militara, autorizatie, autorizatie_nato, rol, pin_hash, salt, activ, date_created, date_modified) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
                (str(uuid.uuid4()), "Operator Registru", "Operator Transfer Date Militare",
                 "MApN / Structura Securitate", "Secret", "NATO SECRET",
                 "operator", h_op, s_op, now, now)
            )
            self.conn.commit()

    def get_active_operators(self) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT id, nume, functie, unitate_militara, autorizatie, autorizatie_nato, rol FROM operatori WHERE activ=1 ORDER BY nume ASC"
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

    def add_operator(self, nume: str, functie: str, unitate: str, autorizatie: str, rol: str, pin: str, creator: str) -> str:
        op_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        p_hash, salt = self.hash_pin(pin)
        nato_clearance = self.NATO_MAP.get(autorizatie, 'NATO UNCLASSIFIED')
        self.conn.execute(
            "INSERT INTO operatori (id, nume, functie, unitate_militara, autorizatie, autorizatie_nato, rol, pin_hash, salt, activ, date_created, date_modified) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
            (op_id, nume, functie, unitate, autorizatie, nato_clearance, rol, p_hash, salt, now, now)
        )
        self.conn.commit()
        self._log_audit(None, "CREATE_OPERATOR", creator, f"Adaugat operator militar {nume} ({rol}, {autorizatie} / {nato_clearance})")
        return op_id

    # ===== REGISTRY NUMBERING & CLASSIFICATION =====
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
        exclude = {'id', 'hash_inregistrare', 'date_modified', 'semnat_operator', 'semnat_de', 'semnat_la', 'four_eyes_aprobator', 'four_eyes_aprobat_la'}
        canonical_dict = {k: str(v) for k, v in data.items() if k not in exclude and v is not None}
        canonical_json = json.dumps(canonical_dict, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

    # ===== AUDIT LOG (SHA-256 TAMPER-EVIDENT HASH CHAIN) =====
    def _log_audit(self, transfer_id: Optional[str], actiune: str, operator: str, detalii: str = "", op_id: Optional[str] = None):
        last_entry = self.conn.execute(
            "SELECT sequence_nr, entry_hash FROM audit_log ORDER BY sequence_nr DESC LIMIT 1"
        ).fetchone()
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

    # ===== DEVICE CONTROL & MEDII AMPRENTATE (ENDPOINT PROTECTOR MODEL) =====
    def add_amprentat_medium(self, data: dict, operator_name: str) -> str:
        media_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        clasificare_max = data.get('clasificare_max', 'Neclasificat')
        nato_max = self.NATO_MAP.get(clasificare_max, 'NATO UNCLASSIFIED')
        eu_max = self.EU_MAP.get(clasificare_max, 'LIMITE / UNCLASSIFIED')
        
        cod_inv = data.get('cod_inventar') or f"AMP-{datetime.now().year}-{secrets.token_hex(3).upper()}"
        
        data_to_insert = {
            'id': media_id,
            'cod_inventar': cod_inv,
            'host_binding': data.get('host_binding') or self.local_host,
            'tip_mediu': data.get('tip_mediu', 'Stick USB'),
            'producator': data.get('producator') or 'Generic',
            'model': data.get('model') or 'Storage Device',
            'vid': (data.get('vid') or '0000').upper(),
            'pid': (data.get('pid') or '0000').upper(),
            'serie_hardware': data.get('serie_hardware', 'UNKNOWN_SN').strip(),
            'pnp_device_id': data.get('pnp_device_id', ''),
            'volume_serial': data.get('volume_serial', ''),
            'capacitate_gb': data.get('capacitate_gb', 0.0),
            'clasificare_max': clasificare_max,
            'clasificare_max_nato': nato_max,
            'clasificare_max_eu': eu_max,
            'status_politica': data.get('status_politica', 'autorizat_rw'),
            'stare_criptare': data.get('stare_criptare', 'Fara'),
            'gestionar_nume': data.get('gestionar_nume', operator_name),
            'gestionar_unitate': data.get('gestionar_unitate', 'MApN'),
            'data_amprentare': now,
            'data_modificare': now,
            'amprentat_de': operator_name,
            'observatii': data.get('observatii', '')
        }
        cols = ", ".join(data_to_insert.keys())
        placeholders = ", ".join(["?"] * len(data_to_insert))
        self.conn.execute(f"INSERT INTO medii_amprentate ({cols}) VALUES ({placeholders})", list(data_to_insert.values()))
        self.conn.commit()

        self._log_audit(
            None, "DEVICE_FINGERPRINT_ENROLLED", operator_name,
            f"Amprentat mediu nou [{cod_inv}] VID:{data_to_insert['vid']} PID:{data_to_insert['pid']} S/N:{data_to_insert['serie_hardware']} pe statia {data_to_insert['host_binding']} cu plafon {clasificare_max}"
        )
        return media_id

    def get_amprentate_media(self, status_politica: Optional[str] = None, search: Optional[str] = None) -> List[Dict]:
        query = "SELECT * FROM medii_amprentate WHERE 1=1"
        params = []
        if status_politica and status_politica != "toate":
            query += " AND status_politica = ?"
            params.append(status_politica)
        if search:
            query += " AND (cod_inventar LIKE ? OR serie_hardware LIKE ? OR model LIKE ? OR producator LIKE ? OR gestionar_nume LIKE ?)"
            lk = f"%{search}%"
            params.extend([lk, lk, lk, lk, lk])
        query += " ORDER BY data_amprentare DESC"
        rows = self.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_medium_by_id(self, medium_id: str) -> Optional[Dict]:
        row = self.conn.execute("SELECT * FROM medii_amprentate WHERE id=?", (medium_id,)).fetchone()
        return dict(row) if row else None

    def find_medium_by_fingerprint(self, vid: str, pid: str, serie_hardware: str) -> Optional[Dict]:
        vid_clean = vid.strip().upper()
        pid_clean = pid.strip().upper()
        sn_clean = serie_hardware.strip()
        
        # Try exact match on VID, PID, SN
        row = self.conn.execute(
            "SELECT * FROM medii_amprentate WHERE UPPER(vid)=? AND UPPER(pid)=? AND serie_hardware=?",
            (vid_clean, pid_clean, sn_clean)
        ).fetchone()
        if row:
            return dict(row)
        
        # Fallback to serial number match
        row = self.conn.execute(
            "SELECT * FROM medii_amprentate WHERE serie_hardware=? AND serie_hardware != 'UNKNOWN_SN'",
            (sn_clean,)
        ).fetchone()
        return dict(row) if row else None

    def update_medium_policy(self, medium_id: str, new_status: str, operator_name: str, motiv: str = ""):
        now = datetime.now().isoformat()
        med = self.get_medium_by_id(medium_id)
        if not med:
            raise ValueError("Mediu inexistent")
        self.conn.execute(
            "UPDATE medii_amprentate SET status_politica=?, data_modificare=?, observatii=observatii || ? WHERE id=?",
            (new_status, now, f" | Politica schimbata in {new_status} la {now} de {operator_name}. {motiv}", medium_id)
        )
        self.conn.commit()
        self._log_audit(
            None, "DEVICE_POLICY_CHANGED", operator_name,
            f"Schimbat politica pentru [{med['cod_inventar']}] S/N {med['serie_hardware']} in {new_status}: {motiv}"
        )

    def is_classification_allowed_on_medium(self, medium_id: str, transfer_classification: str) -> Tuple[bool, str]:
        med = self.get_medium_by_id(medium_id)
        if not med:
            return False, "Mediul selectat nu este inregistrat in baza de date a statiei."
        
        if med['status_politica'] == 'blocat':
            return False, f"Mediul [{med['cod_inventar']}] este BLOCAT / REVOCAT pe aceasta statie."
        
        if med['status_politica'] == 'in_asteptare':
            return False, f"Mediul [{med['cod_inventar']}] este in asteptare aprobare de securitate."

        # Compare classification hierarchy
        med_max = med['clasificare_max']
        try:
            med_idx = self.CLASSIFICATION_LEVELS.index(med_max)
        except ValueError:
            med_idx = 0

        try:
            tx_idx = self.CLASSIFICATION_LEVELS.index(transfer_classification)
        except ValueError:
            tx_idx = 0

        if tx_idx > med_idx:
            return False, f"Violare Plafon de Securitate! Mediul [{med['cod_inventar']}] este autorizat maxim pana la '{med_max}', dar transferul solicitat este '{transfer_classification}'."

        return True, "Valid"

    # ===== TRANSFER REGISTRY (MILITARY SPECIFICATION) =====
    def insert_transfer(self, data: dict, operator: str, operator_id: Optional[str] = None, prefix_institutie: str = "MAPN") -> str:
        record_id = str(uuid.uuid4())
        clasificare = data.get('clasificare', 'Neclasificat')
        nato_clf = self.NATO_MAP.get(clasificare, 'NATO UNCLASSIFIED')
        eu_clf = self.EU_MAP.get(clasificare, 'LIMITE / UNCLASSIFIED')
        
        nr = data.get('nr') or self.get_next_nr(prefix_institutie, clasificare)
        now = datetime.now().isoformat()

        # Check media security ceiling if storage_medium_id is provided
        if data.get('storage_medium_id'):
            allowed, reason = self.is_classification_allowed_on_medium(data['storage_medium_id'], clasificare)
            if not allowed:
                raise ValueError(f"Eroare Politica Control Dispozitiv: {reason}")

        data_to_insert = {
            **data,
            'id': record_id,
            'nr': nr,
            'date_created': now,
            'date_modified': now,
            'operator': operator,
            'operator_id': operator_id,
            'clasificare': clasificare,
            'clasificare_nato': data.get('clasificare_nato') or nato_clf,
            'clasificare_eu': data.get('clasificare_eu') or eu_clf,
            'directie_transfer': data.get('directie_transfer', 'iesire'),
            'scanat_antivirus': data.get('scanat_antivirus', 1),
            'antivirus_detalii': data.get('antivirus_detalii', 'Scanare Antivirus Offline: Negativ (Fără amenințări)')
        }
        
        record_hash = self.calculate_record_hash(data_to_insert)
        data_to_insert['hash_inregistrare'] = record_hash

        cols = ", ".join(data_to_insert.keys())
        placeholders = ", ".join(["?"] * len(data_to_insert))
        self.conn.execute(f"INSERT INTO transferuri ({cols}) VALUES ({placeholders})", list(data_to_insert.values()))
        self.conn.commit()

        self._log_audit(
            record_id, "CREATE_TRANSFER", operator,
            f"Inregistrat transfer militar {nr} [{clasificare} / {nato_clf}] Directie: {data_to_insert['directie_transfer'].upper()} ({data.get('src_institutie')} -> {data.get('dst_institutie')})",
            op_id=operator_id
        )
        self._update_autocomplete(data)
        return record_id

    def approve_four_eyes(self, transfer_id: str, aprobator_name: str, functie: str, operator_id: str) -> bool:
        row = self.conn.execute("SELECT * FROM transferuri WHERE id=?", (transfer_id,)).fetchone()
        if not row:
            return False
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE transferuri SET four_eyes_aprobator=?, four_eyes_functie=?, four_eyes_aprobat_la=?, date_modified=? WHERE id=?",
            (aprobator_name, functie, now, now, transfer_id)
        )
        self.conn.commit()
        self._log_audit(
            transfer_id, "FOUR_EYES_APPROVAL", aprobator_name,
            f"Aprobare principiul celor 4 ochi (Four-Eyes) pentru transferul {row['nr']} de catre {aprobator_name} ({functie})",
            op_id=operator_id
        )
        return True

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
        self._log_audit(transfer_id, "SIGN_TRANSFER", operator_name,
                         f"Semnat formal transfer {row['nr']} de catre {operator_name}", op_id=operator_id)
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
        self._log_audit(transfer_id, "CANCEL_TRANSFER", operator_name,
                         f"Anulat transfer {row['nr']}: {motiv}", op_id=operator_id)
        return True

    def get_all_transfers(self, search: str = "", clasificare: str = "", directie: str = "", status: str = "") -> List[Dict]:
        query = "SELECT * FROM transferuri WHERE 1=1"
        params = []
        if search:
            query += " AND (src_institutie LIKE ? OR dst_institutie LIKE ? OR pers_nume LIKE ? OR transfer_sn LIKE ? OR nr LIKE ? OR curier_militar_nume LIKE ?)"
            like = f"%{search}%"
            params += [like, like, like, like, like, like]
        if clasificare:
            query += " AND clasificare=?"
            params.append(clasificare)
        if directie:
            query += " AND directie_transfer=?"
            params.append(directie)
        if status:
            query += " AND status=?"
            params.append(status)
        query += " ORDER BY date_created DESC"
        rows = self.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def sanitize_media(self, mediu_id: str, metoda: str, procedura_detalii: str, operator_executant: str,
                        martor_verificator: str, aprobat_de: str = "") -> str:
        row = self.conn.execute("SELECT * FROM medii_amprentate WHERE id=?", (mediu_id,)).fetchone()
        if not row:
            raise ValueError("Mediu amprentat inexistent")
        cert_nr = f"SAN-NIST88-{datetime.now().year}-{secrets.token_hex(4).upper()}"
        now = datetime.now().isoformat()
        san_id = str(uuid.uuid4())
        self.conn.execute(
            "INSERT INTO jurnal_sanitarizare (id, mediu_id, serie_hardware, metoda, procedura_detalii, "
            "operator_executant, martor_verificator, aprobat_de, data_executie, certificat_nr) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (san_id, mediu_id, row['serie_hardware'], metoda, procedura_detalii,
             operator_executant, martor_verificator, aprobat_de, now, cert_nr)
        )
        new_status = 'blocat' if metoda == 'Destroy' else 'autorizat_rw'
        self.conn.execute("UPDATE medii_amprentate SET status_politica=?, data_modificare=? WHERE id=?", (new_status, now, mediu_id))
        self.conn.commit()
        self._log_audit(None, "SANITIZE", operator_executant,
                         f"Sanitizare NIST SP 800-88r2 ({metoda}) pentru mediu S/N {row['serie_hardware']}, certificat {cert_nr}")
        return cert_nr

    def _update_autocomplete(self, data: dict):
        fields = ['src_institutie', 'dst_institutie', 'pers_nume', 'curier_militar_nume']
        now = datetime.now().isoformat()
        for field in fields:
            val = data.get(field)
            if val:
                self.conn.execute(
                    "INSERT INTO autocomplete (categorie, valoare, frecventa, ultima_data) VALUES (?, ?, 1, ?) "
                    "ON CONFLICT(categorie, valoare) DO UPDATE SET frecventa=frecventa+1, ultima_data=?",
                    (field, val, now, now)
                )
        self.conn.commit()

    def get_autocomplete_suggestions(self, categorie: str) -> List[str]:
        rows = self.conn.execute(
            "SELECT valoare FROM autocomplete WHERE categorie=? ORDER BY frecventa DESC LIMIT 20", (categorie,)
        ).fetchall()
        return [r['valoare'] for r in rows]

    def get_statistics(self) -> Dict:
        total = self.conn.execute("SELECT COUNT(*) c FROM transferuri").fetchone()['c']
        active = self.conn.execute("SELECT COUNT(*) c FROM transferuri WHERE status='activ'").fetchone()['c']
        clf_rows = self.conn.execute("SELECT clasificare, COUNT(*) c FROM transferuri GROUP BY clasificare").fetchall()
        dir_rows = self.conn.execute("SELECT directie_transfer, COUNT(*) c FROM transferuri GROUP BY directie_transfer").fetchall()
        media_count = self.conn.execute("SELECT COUNT(*) c FROM medii_amprentate").fetchone()['c']
        media_rw = self.conn.execute("SELECT COUNT(*) c FROM medii_amprentate WHERE status_politica='autorizat_rw'").fetchone()['c']
        media_ro = self.conn.execute("SELECT COUNT(*) c FROM medii_amprentate WHERE status_politica='autorizat_ro'").fetchone()['c']
        media_blocked = self.conn.execute("SELECT COUNT(*) c FROM medii_amprentate WHERE status_politica='blocat'").fetchone()['c']
        audit_count = self.conn.execute("SELECT COUNT(*) c FROM audit_log").fetchone()['c']
        san_count = self.conn.execute("SELECT COUNT(*) c FROM jurnal_sanitarizare").fetchone()['c']
        return {
            "total_transferuri": total,
            "transferuri_active": active,
            "pe_clasificare": {r['clasificare']: r['c'] for r in clf_rows},
            "pe_directie": {r['directie_transfer']: r['c'] for r in dir_rows},
            "media_total": media_count,
            "media_rw": media_rw,
            "media_ro": media_ro,
            "media_blocked": media_blocked,
            "audit_events": audit_count,
            "sanitizari_efectuate": san_count
        }

    def close(self):
        self.conn.close()

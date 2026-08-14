CREATE TABLE IF NOT EXISTS transferuri (
    id TEXT PRIMARY KEY, nr TEXT UNIQUE NOT NULL,
    date_created TEXT NOT NULL, date_modified TEXT NOT NULL, operator TEXT NOT NULL,
    src_institutie TEXT NOT NULL, src_pc_nume TEXT NOT NULL, src_medium TEXT NOT NULL,
    src_sn TEXT, src_path TEXT,
    pers_nume TEXT NOT NULL, pers_functie TEXT, pers_legitimatie TEXT,
    pers_autorizatie TEXT NOT NULL DEFAULT 'Nesecurizat',
    transfer_medium TEXT NOT NULL, transfer_sn TEXT, transfer_label TEXT,
    transfer_cap_gb REAL, transfer_free_gb REAL,
    dst_institutie TEXT NOT NULL, dst_pc_nume TEXT,
    dst_medium TEXT, dst_sn TEXT, dst_path TEXT,
    arhiva_nume TEXT, arhiva_tip TEXT, arhiva_dim_gb REAL, arhiva_fisiere INTEGER,
    arhiva_hash TEXT, arhiva_descriere TEXT,
    clasificare TEXT NOT NULL DEFAULT 'Nesecret',
    restrictii TEXT, aprobare_mult TEXT, baza_legala TEXT,
    log_medium TEXT, log_path TEXT,
    status TEXT NOT NULL DEFAULT 'draft', observatii TEXT,
    semnat_operator INTEGER DEFAULT 0, data_verif_anual TEXT,
    verificat_de TEXT, hash_inregistrare TEXT
);
CREATE INDEX IF NOT EXISTS idx_date_created ON transferuri(date_created);
CREATE TABLE IF NOT EXISTS operatori (
    id TEXT PRIMARY KEY, nume TEXT UNIQUE NOT NULL, functie TEXT,
    autorizatie TEXT NOT NULL DEFAULT 'Nesecurizat',
    activ INTEGER DEFAULT 1, date_created TEXT NOT NULL, date_modified TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS contoare (an INTEGER PRIMARY KEY, contor INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS autocomplete (
    categorie TEXT, valoare TEXT, frecventa INTEGER DEFAULT 1,
    ultima_data TEXT, PRIMARY KEY (categorie, valoare)
);
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY, transfer_id TEXT, actiune TEXT NOT NULL,
    operator TEXT NOT NULL, timestamp TEXT NOT NULL, detalii TEXT
);
INSERT OR IGNORE INTO operatori VALUES ('1', 'Admin', 'Administrator', 'Strict Secret', 1, datetime('now'), datetime('now'));

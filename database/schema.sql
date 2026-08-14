-- Registru Transferuri Media v3.1
-- Conformitate: HG 585/2002, Legea 182/2002, HG 781/2002, NIST SP 800-88 Rev.2, IEEE 2883-2022

CREATE TABLE IF NOT EXISTS transferuri (
    id TEXT PRIMARY KEY,
    nr TEXT UNIQUE NOT NULL,
    date_created TEXT NOT NULL,
    date_modified TEXT NOT NULL,
    operator TEXT NOT NULL,
    operator_id TEXT,
    src_institutie TEXT NOT NULL,
    src_pc_nume TEXT NOT NULL,
    src_medium TEXT NOT NULL,
    src_sn TEXT,
    src_path TEXT,
    pers_nume TEXT NOT NULL,
    pers_functie TEXT,
    pers_legitimatie TEXT,
    pers_autorizatie TEXT NOT NULL DEFAULT 'Neclasificat',
    transfer_medium TEXT NOT NULL,
    transfer_sn TEXT,
    transfer_label TEXT,
    transfer_cap_gb REAL,
    transfer_free_gb REAL,
    storage_medium_id TEXT,
    dst_institutie TEXT NOT NULL,
    dst_pc_nume TEXT,
    dst_medium TEXT,
    dst_sn TEXT,
    dst_path TEXT,
    arhiva_nume TEXT,
    arhiva_tip TEXT,
    arhiva_dim_gb REAL,
    arhiva_fisiere INTEGER,
    arhiva_hash TEXT,
    arhiva_descriere TEXT,
    clasificare TEXT NOT NULL DEFAULT 'Neclasificat',
    clasificare_eu TEXT,
    restrictii TEXT,
    aprobare_mult TEXT,
    baza_legala TEXT,
    nr_aprobare TEXT,
    nr_exemplare INTEGER DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'activ',
    motiv_anulare TEXT,
    observatii TEXT,
    semnat_operator INTEGER DEFAULT 0,
    semnat_de TEXT,
    semnat_la TEXT,
    data_verif_anual TEXT,
    verificat_de TEXT,
    hash_inregistrare TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transferuri_date ON transferuri(date_created);
CREATE INDEX IF NOT EXISTS idx_transferuri_clasificare ON transferuri(clasificare);
CREATE INDEX IF NOT EXISTS idx_transferuri_status ON transferuri(status);
CREATE INDEX IF NOT EXISTS idx_transferuri_nr ON transferuri(nr);

CREATE TABLE IF NOT EXISTS operatori (
    id TEXT PRIMARY KEY,
    nume TEXT UNIQUE NOT NULL,
    functie TEXT,
    autorizatie TEXT NOT NULL DEFAULT 'Neclasificat',
    rol TEXT NOT NULL DEFAULT 'operator',
    pin_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    activ INTEGER DEFAULT 1,
    date_created TEXT NOT NULL,
    date_modified TEXT NOT NULL,
    last_login TEXT
);

CREATE TABLE IF NOT EXISTS medii_stocare (
    id TEXT PRIMARY KEY,
    cod_inventar TEXT UNIQUE NOT NULL,
    tip_mediu TEXT NOT NULL,
    producator TEXT,
    model TEXT,
    serie_hardware TEXT NOT NULL,
    vid TEXT,
    pid TEXT,
    capacitate_gb REAL,
    clasificare_max TEXT NOT NULL DEFAULT 'Neclasificat',
    status TEXT NOT NULL DEFAULT 'activ',
    locatie_fizica TEXT,
    gestionar TEXT,
    data_inregistrare TEXT NOT NULL,
    data_modificare TEXT NOT NULL,
    observatii TEXT
);

CREATE INDEX IF NOT EXISTS idx_medii_sn ON medii_stocare(serie_hardware);
CREATE INDEX IF NOT EXISTS idx_medii_status ON medii_stocare(status);

CREATE TABLE IF NOT EXISTS jurnal_sanitarizare (
    id TEXT PRIMARY KEY,
    mediu_id TEXT NOT NULL,
    serie_hardware TEXT NOT NULL,
    metoda TEXT NOT NULL,
    standard_referinta TEXT NOT NULL DEFAULT 'NIST SP 800-88 Rev. 2 (2025) / IEEE 2883-2022',
    procedura_detalii TEXT NOT NULL,
    tip_cheie_ce TEXT,
    putere_securitate_biti INTEGER,
    verificat INTEGER DEFAULT 0,
    verificat_de TEXT,
    verificat_la TEXT,
    validat INTEGER DEFAULT 0,
    validat_de TEXT,
    validat_la TEXT,
    operator_executant TEXT NOT NULL,
    martor_verificator TEXT NOT NULL,
    aprobat_de TEXT,
    data_executie TEXT NOT NULL,
    certificat_nr TEXT UNIQUE NOT NULL,
    rezultat TEXT NOT NULL DEFAULT 'succes',
    observatii TEXT,
    FOREIGN KEY(mediu_id) REFERENCES medii_stocare(id)
);

CREATE TABLE IF NOT EXISTS contoare (
    an INTEGER NOT NULL,
    clasificare TEXT NOT NULL,
    contor INTEGER DEFAULT 0,
    PRIMARY KEY (an, clasificare)
);

CREATE TABLE IF NOT EXISTS autocomplete (
    categorie TEXT NOT NULL,
    valoare TEXT NOT NULL,
    frecventa INTEGER DEFAULT 1,
    ultima_data TEXT NOT NULL,
    PRIMARY KEY (categorie, valoare)
);

CREATE TABLE IF NOT EXISTS audit_log (
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
);

CREATE INDEX IF NOT EXISTS idx_audit_seq ON audit_log(sequence_nr);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(timestamp);

CREATE TABLE IF NOT EXISTS audit_checkpoints (
    id TEXT PRIMARY KEY,
    data_checkpoint TEXT NOT NULL,
    seq_start INTEGER NOT NULL,
    seq_end INTEGER NOT NULL,
    merkle_root TEXT,
    final_chain_hash TEXT NOT NULL,
    operator TEXT NOT NULL,
    semnat_la TEXT NOT NULL
);

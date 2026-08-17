-- Registru Transferuri Media v3.1 (Conformitate MApN / HG 585/2002, NATO AC/35, EUCI 2013/488/UE, NIST SP 800-88r2)
-- Endpoint Protector Device Control & Military Registry Schema

CREATE TABLE IF NOT EXISTS transferuri (
    id TEXT PRIMARY KEY,
    nr TEXT UNIQUE NOT NULL,
    date_created TEXT NOT NULL,
    date_modified TEXT NOT NULL,
    operator TEXT NOT NULL,
    operator_id TEXT,
    directie_transfer TEXT NOT NULL DEFAULT 'iesire', -- iesire, intrare, tranzit
    
    -- Sursa
    src_institutie TEXT NOT NULL,
    src_pc_nume TEXT NOT NULL,
    src_medium TEXT NOT NULL,
    src_sn TEXT,
    src_path TEXT,
    
    -- Persoana / Curier militar
    pers_nume TEXT NOT NULL,
    pers_functie TEXT,
    pers_legitimatie TEXT,
    pers_autorizatie TEXT NOT NULL DEFAULT 'Neclasificat',
    curier_militar_nume TEXT,
    curier_militar_legitimatie TEXT,
    
    -- Mediu de transfer (legat de medii_amprentate)
    transfer_medium TEXT NOT NULL,
    transfer_sn TEXT,
    transfer_label TEXT,
    transfer_vid TEXT,
    transfer_pid TEXT,
    transfer_cap_gb REAL,
    transfer_free_gb REAL,
    storage_medium_id TEXT,
    
    -- Destinatie
    dst_institutie TEXT NOT NULL,
    dst_pc_nume TEXT,
    dst_medium TEXT,
    dst_sn TEXT,
    dst_path TEXT,
    
    -- Continut & Integritate Date
    arhiva_nume TEXT,
    arhiva_tip TEXT,
    arhiva_dim_gb REAL,
    arhiva_fisiere INTEGER,
    arhiva_hash TEXT,
    arhiva_descriere TEXT,
    scanat_antivirus INTEGER DEFAULT 1,
    antivirus_detalii TEXT DEFAULT 'Scanare Antivirus Offline: Negativ (Fără amenințări)',
    
    -- Clasificare & Conformitate
    clasificare TEXT NOT NULL DEFAULT 'Neclasificat',
    clasificare_nato TEXT NOT NULL DEFAULT 'NATO UNCLASSIFIED',
    clasificare_eu TEXT NOT NULL DEFAULT 'LIMITE / UNCLASSIFIED',
    restrictii TEXT,
    aprobare_mult TEXT,
    baza_legala TEXT,
    nr_aprobare TEXT,
    nr_exemplare INTEGER DEFAULT 1,
    
    -- Aprobare Four-Eyes (Principiul celor 4 ochi - HG 585 / NATO AC/35)
    four_eyes_aprobator TEXT,
    four_eyes_functie TEXT,
    four_eyes_aprobat_la TEXT,
    
    -- Status & Semnaturi
    status TEXT NOT NULL DEFAULT 'activ', -- activ, anulat, arhivat
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
CREATE INDEX IF NOT EXISTS idx_transferuri_directie ON transferuri(directie_transfer);

-- Baza de date Medii de Stocare Amprentate (Device Control Whitelist - Endpoint Protector Model)
CREATE TABLE IF NOT EXISTS medii_amprentate (
    id TEXT PRIMARY KEY,
    cod_inventar TEXT UNIQUE NOT NULL,
    denumire_custom TEXT, -- Nume prietenos/personalizat (in loc de Local Disk)
    host_binding TEXT NOT NULL, -- Numele/ID-ul statiei locale autorizate
    tip_mediu TEXT NOT NULL, -- Stick USB, SSD Extern, HDD Extern, Mediu Optic Securizat, Card SD
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
    status_politica TEXT NOT NULL DEFAULT 'autorizat_rw', -- autorizat_rw, autorizat_ro, blocat, in_asteptare
    stare_criptare TEXT NOT NULL DEFAULT 'Fara', -- Fara, BitLocker, SED_Opal, Omologat_ORNISS
    gestionar_nume TEXT,
    gestionar_unitate TEXT,
    data_amprentare TEXT NOT NULL,
    data_modificare TEXT NOT NULL,
    amprentat_de TEXT NOT NULL,
    observatii TEXT
);

CREATE INDEX IF NOT EXISTS idx_medii_amp_sn ON medii_amprentate(serie_hardware);
CREATE INDEX IF NOT EXISTS idx_medii_amp_vid_pid ON medii_amprentate(vid, pid);
CREATE INDEX IF NOT EXISTS idx_medii_amp_status ON medii_amprentate(status_politica);
CREATE INDEX IF NOT EXISTS idx_medii_amp_host ON medii_amprentate(host_binding);

-- Jurnal de Sanitizare Conform NIST SP 800-88 Rev. 2 (2025) / IEEE 2883-2022
CREATE TABLE IF NOT EXISTS jurnal_sanitarizare (
    id TEXT PRIMARY KEY,
    mediu_id TEXT NOT NULL,
    serie_hardware TEXT NOT NULL,
    metoda TEXT NOT NULL, -- Clear, Purge, Destroy
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
    FOREIGN KEY(mediu_id) REFERENCES medii_amprentate(id)
);

CREATE TABLE IF NOT EXISTS operatori (
    id TEXT PRIMARY KEY,
    nume TEXT UNIQUE NOT NULL,
    functie TEXT,
    unitate_militara TEXT DEFAULT 'MApN / Structura Securitate',
    autorizatie TEXT NOT NULL DEFAULT 'Neclasificat',
    autorizatie_nato TEXT NOT NULL DEFAULT 'NATO UNCLASSIFIED',
    rol TEXT NOT NULL DEFAULT 'operator', -- admin, ofiter_securitate, operator
    pin_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    activ INTEGER DEFAULT 1,
    date_created TEXT NOT NULL,
    date_modified TEXT NOT NULL,
    last_login TEXT
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

-- Jurnal de Audit Criptografic (Tamper-Evident SHA-256 Hash Chain)
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

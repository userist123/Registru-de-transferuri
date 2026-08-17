"""
Cognitive Bridge Service - Punte de Integrare intre Registrul Militar si AI Memory Vault
Leaga Registrul de Transferuri de Sistemul Cognitiv de Memorie (AI_Memory_Vault_CODEX_READY):
- Ingestie si sinteza automata a transferurilor finalizate in 06_INBOX / 01_KNOWLEDGE (Conformitate P0-P15)
- Oracol cognitiv de securitate militar pentru interogarea procedurilor HG 585, NATO AC/35 si NIST 800-88r2
- Audit forensic incrucisat: Amprenta Hardware Windows + Hash Payload + Jurnal Audit Seif
"""
import os, sys, uuid, json, hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from database.db import DatabaseManager

# Path catre AI Memory Vault
VAULT_ROOT = r"c:\Users\Marius\Documents\Codex\AI_Memory_Vault_CODEX_READY"
if os.path.exists(VAULT_ROOT) and VAULT_ROOT not in sys.path:
    sys.path.insert(0, VAULT_ROOT)


class CognitiveBridgeService:
    def __init__(self, db_manager: DatabaseManager, vault_path: str = VAULT_ROOT):
        self.db = db_manager
        self.vault_path = vault_path
        self.vault_connected = False
        self.controller = None
        self.storage = None
        self._init_vault_connection()

    def _init_vault_connection(self):
        try:
            if not os.path.exists(self.vault_path):
                self.vault_connected = False
                return

            from memory_controller.storage.sqlite_engine import SQLiteStorageEngine
            from memory_controller.controller import MemoryController
            
            db_file = os.path.join(self.vault_path, "vault_memory.sqlite3")
            self.storage = SQLiteStorageEngine(db_file, wal_mode=True)
            self.controller = MemoryController(self.storage)
            self.vault_connected = True
        except Exception as e:
            self.vault_connected = False

    def is_connected(self) -> bool:
        return self.vault_connected

    def search_vault_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Cauta in baza de cunostinte canonice a Seifului de Memorie."""
        if not self.vault_connected or not self.controller:
            return self._offline_fallback_search(query)

        try:
            from memory_controller.authorizer import Principal
            pack = self.controller.search(Principal.AI_AGENT, query, page_size=limit)
            return pack.get('results', [])
        except Exception:
            return self._offline_fallback_search(query)

    def _offline_fallback_search(self, query: str) -> List[Dict[str, Any]]:
        """Fallback inteligent pe fisierele de documentatie markdown din Seif daca motorul SQLite e ocupat."""
        results = []
        q_lower = query.lower()
        search_dirs = [
            os.path.join(self.vault_path, "00_CORE"),
            os.path.join(self.vault_path, "01_KNOWLEDGE"),
            os.path.join(self.vault_path, "03_PROCEDURES")
        ]
        for sdir in search_dirs:
            if not os.path.exists(sdir):
                continue
            for fname in os.listdir(sdir):
                if fname.endswith(".md"):
                    fpath = os.path.join(sdir, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            if q_lower in content.lower() or q_lower in fname.lower():
                                results.append({
                                    "id": fname,
                                    "category": os.path.basename(sdir),
                                    "title": fname.replace(".md", "").replace("_", " "),
                                    "content": content[:400] + "..."
                                })
                    except Exception:
                        pass
        return results[:5]

    def ask_security_oracle(self, question: str) -> str:
        """
        Oracol Cognitiv: Raspunde la intrebarile ofiterilor de securitate si operatorilor
        privind procedurile HG 585/2002, standardele NATO AC/35, EUCI si sanitizarea NIST.
        """
        q = question.lower()

        # 1. Sanitizare NIST SP 800-88r2
        if "sanitiz" in q or "nist" in q or "stergere" in q or "distrugere" in q or "purge" in q or "clear" in q:
            return (
                "🛡️ <b>Normativ Sanitizare Conform NIST SP 800-88 Rev. 2 (2025) & IEEE 2883-2022:</b><br><br>"
                "• <b>Nivel NECLASIFICAT:</b> Metoda <code>Clear</code> (Suprascriere logică 1-pass a tuturor sectoarelor adresabile).<br>"
                "• <b>Nivel SECRET DE SERVICIU (NATO RESTRICTED):</b> Metoda <code>Purge</code> (Cryptographic Erase pe dispozitive SED TCG Opal sau suprascriere multi-pass cu verificare 100%).<br>"
                "• <b>Nivel SECRET & STRICT SECRET (NATO SECRET / COSMIC TOP SECRET):</b> Metoda <code>Destroy</code> (Dezintegrare fizică / tocare conform standardului DIN 66399 clasa H-5 cu particule < 10 mm²).<br><br>"
                "<i>Notă: Orice operațiune de sanitizare generează un Certificat Unic semnat de operator și martor verificator.</i>"
            )

        # 2. Numerotare HG 585 Art. 41
        if "numerotar" in q or "prefix" in q or "hg 585" in q or "art. 41" in q or "art 41" in q or "numar" in q:
            return (
                "📋 <b>Reguli de Numerotare a Transferurilor conform HG 585/2002 (Art. 41):</b><br><br>"
                "Fiecare număr de înregistrare militar trebuie să conțină prefixul obligatoriu corespunzător nivelului:<br>"
                "• <code>000</code> — <b>Strict Secret de Importanță Deosebită (SSID)</b> (Ex: <code>MAPN-2026-000-0001</code>)<br>"
                "• <code>00</code> — <b>Strict Secret (SS)</b> (Ex: <code>MAPN-2026-00-0001</code>)<br>"
                "• <code>0</code> — <b>Secret (S)</b> (Ex: <code>MAPN-2026-0-0001</code>)<br>"
                "• <code>S</code> — <b>Secret de Serviciu (SSV)</b> (Ex: <code>MAPN-2026-S-0001</code>)<br>"
                "• <code>NC</code> — <b>Neclasificat</b> (Ex: <code>MAPN-2026-NC-0001</code>)<br><br>"
                "<i>Sistemul permite și introducerea numerelor personalizate de unitate (ex: <code>2150-23SSv</code>).</i>"
            )

        # 3. Clasificare NATO & UE
        if "nato" in q or "ue" in q or "euci" in q or "clearance" in q or "cosmic" in q:
            return (
                "🌐 <b>Grila de Echivalență Națională, NATO (AC/35) & Uniunea Europeană (2013/488/UE):</b><br><br>"
                "1. <b>Strict Secret de Importanță Deosebită (SSID)</b> ➔ <code>COSMIC TOP SECRET</code> ➔ <code>TRÈS SECRET UE / EU TOP SECRET</code><br>"
                "2. <b>Strict Secret (SS)</b> ➔ <code>NATO SECRET</code> ➔ <code>SECRET UE / EU SECRET</code><br>"
                "3. <b>Secret (S)</b> ➔ <code>NATO CONFIDENTIAL</code> ➔ <code>CONFIDENTIEL UE / EU CONFIDENTIAL</code><br>"
                "4. <b>Secret de Serviciu (SSV)</b> ➔ <code>NATO RESTRICTED</code> ➔ <code>RESTREINT UE / EU RESTRICTED</code><br>"
                "5. <b>Neclasificat</b> ➔ <code>NATO UNCLASSIFIED</code> ➔ <code>LIMITE / UNCLASSIFIED</code>"
            )

        # 4. Principiul celor 4 Ochi (Four-Eyes Principle)
        if "4 ochi" in q or "four eyes" in q or "aprobator" in q or "contrasemnare" in q or "martor" in q:
            return (
                "👥 <b>Principiul celor 4 Ochi (Four-Eyes Principle) în Sistemele Clasificate:</b><br><br>"
                "• Pentru transferurile cu nivelurile <b>Secret</b>, <b>Strict Secret</b> și <b>SSID</b>, sistemul impune obligatoriu autentificarea a <b>doi utilizatori distincți</b>:<br>"
                "  1. <i>Operatorul inițiator</i> (care generează pachetul și calculează hash-ul SHA-256).<br>"
                "  2. <i>Ofițerul de securitate / Martorul verificator</i> (care introduce PIN-ul securizat de 6 cifre pentru validare).<br>"
                "• Fără aprobarea 4-Eyes, transferul este blocat și nu poate fi efectuat pe mediul amovibil."
            )

        # 5. Device Control & Amprentare
        if "amprent" in q or "vid" in q or "pid" in q or "device control" in q or "whitelist" in q or "stick" in q:
            return (
                "🔒 <b>Politica de Control Dispozitive (Endpoint Protector Model):</b><br><br>"
                "• Fiecare mediu amovibil (USB, CD/DVD, SSD extern, card SD) este legat de stația locală prin amprenta hardware imutabilă: <code>VID</code>, <code>PID</code>, <code>Serie Hardware Firmware (S/N)</code>.<br>"
                "• Transferul este autorizat doar dacă nivelul de clasificare al transferului este <b>inferior sau egal cu plafonul de securitate autorizat</b> al mediului.<br>"
                "• Datele fizice nu pot fi modificate manual; utilizatorul poate personaliza exclusiv <i>Denumirea Volumului</i> și <i>Numărul de Înregistrare din Registrul de Medii</i>."
            )

        # Default knowledge search from Vault
        vault_hits = self.search_vault_knowledge(question, limit=2)
        if vault_hits:
            hit_texts = "<br><br>".join([f"• <b>{h.get('title', h.get('id'))}:</b> {h.get('content', '')[:200]}" for h in vault_hits])
            return f"📚 <b>Informații relevante identificate în Seiful de Memorie:</b><br><br>{hit_texts}"

        return (
            "ℹ️ <b>Sistem de Asistență INFOSEC & Registru Transferuri:</b><br>"
            "Puteți adresa întrebări despre: <i>normele de sanitizare NIST 800-88r2</i>, <i>clasificările NATO/UE</i>, <i>numerotarea HG 585 Art. 41</i>, <i>principiul celor 4 ochi</i> sau <i>politicile de control al mediilor de stocare</i>."
        )

    def synthesize_transfer_to_vault_memory(self, transfer_id: str, operator_name: str) -> Tuple[bool, str]:
        """
        Sintetizeaza un transfer militar finalizat intr-o nota canonica de memorie (in 06_INBOX/RAW_IMPORTS/
        si propune inregistrarea catre MemoryController conform invariantelor P0-P15).
        """
        tx = self.db.get_transfer_by_id(transfer_id)
        if not tx:
            return False, "Transferul militar nu a fost găsit în baza de date locală."

        note_id = str(uuid.uuid4())
        now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        now_ts = datetime.now(timezone.utc).isoformat()

        # Frontmatter canonic si continut conform AGENTS.md
        note_content = f"""---
id: "{note_id}"
type: "experience"
lifecycle: "REVIEW"
category: "Transferuri_Militare"
tags: ["transfer_date", "militar", "hg585", "{tx.get('clasificare', 'neclasificat').lower()}", "device_control"]
created: "{now_date}"
updated: "{now_date}"
provenance:
  source_type: "execution"
  source_ref: "MAPN_DEVICE_CONTROL_STATIE_{self.db.local_host}"
confidence: "high"
verification: "unverified"
relations: []
---

# Raport Operativ Transfer Date: {tx.get('nr')}

## 1. Identificare & Clasificare
- **Număr Înregistrare:** {tx.get('nr')}
- **Data Execuției:** {tx.get('date_created')}
- **Nivel Clasificare:** {tx.get('clasificare')} (NATO: {tx.get('clasificare_nato')}, UE: {tx.get('clasificare_eu')})
- **Direcție Flux:** {tx.get('directie_transfer', 'iesire').upper()}
- **Stație Sursă:** {tx.get('src_pc_nume')} (Host ID: {self.db.local_host})

## 2. Pachet Date & Integritate Criptografică
- **Denumire Pachet / Arhivă:** `{tx.get('arhiva_nume')}`
- **Tip Conținut:** {tx.get('arhiva_tip')} ({tx.get('arhiva_dim_gb', 0)} GB, {tx.get('arhiva_fisiere', 1)} fișiere)
- **Hash SHA-256 Date:** `{tx.get('arhiva_hash')}`
- **Hash Înregistrare Audit:** `{tx.get('hash_inregistrare')}`
- **Status Antivirus:** {tx.get('antivirus_detalii', 'Scanare negativă')}

## 3. Suport Memorie & Telemetrie Hardware
- **Tip Mediu:** {tx.get('transfer_medium')}
- **Denumire Volum / Etichetă:** {tx.get('transfer_label', 'N/A')}
- **Serie Hardware Firmware (S/N):** `{tx.get('transfer_sn', 'N/A')}`
- **Identificator Hardware:** `VID_{tx.get('transfer_vid', 'N/A')} & PID_{tx.get('transfer_pid', 'N/A')}`

## 4. Lanț de Custodie & Semnături
- **Persoană Responsabilă:** {tx.get('pers_nume')} ({tx.get('pers_functie', 'Operator')}) - Legitimație: {tx.get('pers_legitimatie', 'N/A')}
- **Curier Militar:** {tx.get('curier_militar_nume', 'Fără curier extern')} (Permis: {tx.get('curier_militar_legitimatie', 'N/A')})
- **Operator Înregistrare:** {tx.get('operator')}
- **Contrasemnare Four-Eyes:** {tx.get('four_eyes_aprobator', 'N/A')} ({tx.get('four_eyes_functie', 'N/A')})

---
*Notă generată automat de Puntea Cognitivă a Registrului de Transferuri MApN în Seiful de Memorie AI.*
"""

        # 1. Salvare in 06_INBOX/RAW_IMPORTS/
        inbox_dir = os.path.join(self.vault_path, "06_INBOX", "RAW_IMPORTS")
        os.makedirs(inbox_dir, exist_ok=True)
        raw_file_name = f"Transfer_{tx.get('nr').replace('/', '_').replace('-', '_')}_{now_date}.md"
        raw_file_path = os.path.join(inbox_dir, raw_file_name)
        
        try:
            with open(raw_file_path, "w", encoding="utf-8") as f:
                f.write(note_content)
        except Exception as e:
            return False, f"Eroare scriere fișier inbox: {e}"

        # 2. Propunere catre MemoryController daca este disponibil
        if self.vault_connected and self.controller:
            try:
                from memory_controller.authorizer import Principal
                note_dict = {
                    "id": note_id,
                    "type": "experience",
                    "lifecycle": "REVIEW",
                    "category": "Transferuri_Militare",
                    "tags": ["transfer_date", "militar", "hg585", tx.get('clasificare', 'neclasificat').lower()],
                    "created": now_date,
                    "updated": now_date,
                    "provenance": {
                        "source_type": "execution",
                        "source_ref": f"MAPN_TRANSFER_{tx.get('nr')}"
                    },
                    "confidence": "high",
                    "verification": "unverified",
                    "relations": [],
                    "content": note_content
                }
                self.controller.propose(Principal.AI_AGENT, note_dict)
            except Exception as e:
                pass

        return True, f"Transferul [{tx.get('nr')}] a fost sintetizat în Seiful de Memorie!\nFișier: {raw_file_name}\nStatus: REVIEW (Pregătit pentru atestare)"

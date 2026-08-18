# MODEL DE SECURITATE & THREAT MODELING — REGISTRU DE TRANSFERURI v5.3

**Standarde de conformitate:** HG 585/2002, NATO AC/35-D/1022, EUCI 2013/488/UE, NIST SP 800-88r2, IEEE 2883-2022.

---

## 1. Constrângeri & Concepte de Bază (Air-Gap)
- **Zero Rețea**: Aplicația nu inițiază niciun apel de rețea extern și nu include telemetrie.
- **Bază de date locală criptată**: Baza SQLite funcționează în modul WAL cu tranzacții atomice `BEGIN IMMEDIATE`, fiind protejată la nivel de cheie prin DPAPI (Data Protection API) la nivel de mașină (`CurrentUser` / `LocalMachine`).
- **Audit Criptografic SHA-256 Imutabil**: Orice operațiune (autentificare, adăugare transfer, evaluare mediu, modificare denumire, generare PV) este înlănțuită criptografic `Hash(Bloc_N) = SHA256(Seq | Timestamp | Action | Operator | Details | Hash(Bloc_N-1))`.

---

## 2. Hardening Identitate & Autentificare
1. **Derivare PIN cu Argon2id**:
   - Algoritm: Argon2id (Memory-hard KDF).
   - Parametri de securitate: `Memory = 64 MB`, `Iterations = 3`, `Parallelism = 4`, `Salt = 16 bytes cryptographically secure`.
2. **Autorizare Duală în 4-Ochi (Four-Eyes Principle)**:
   - Pentru transferurile clasificate la nivel *Secret*, *Strict Secret* sau *Strict Secret de Importanță Deosebită (SSID)*, este cerută obligatoriu aprobarea unui al doilea ofițer de securitate cu clearance echivalent sau superior.
   - **Semnătură Criptografică HMAC-SHA256**: Se generează un jeton de atestare bazat pe cheia derivată a martorului și se include în blocul de audit.

---

## 3. Controlul Dispozitivelor (Invariantele P16–P18 & Endpoint Protection)
- **P16 — Imutabilitatea Telemetriei Hardware**:
  - Seria fizică de firmware (S/N), VID:PID, modelul fabricii și capacitatea sunt extrase direct din sistemul de operare prin WMI / PnP și sunt strict **Read-Only**.
- **P17 — Izolarea Denumirii Prietenoase**:
  - Utilizatorul poate actualiza exclusiv denumirea logică / numărul de înregistrare HG 585 al volumului, fără a altera vreun bit din amprenta fizică.
- **P18 — Trasabilitate & Chain of Custody**:
  - Orice transfer consemnează identificatorul hardware neschimbat al suportului fizic.
- **Politici de Porturi USB (DevicePolicyEnforcer)**:
  - *Blocare Totală USB*: `USBSTOR Start = 4`.
  - *Mod Doar-Citire*: `StorageDevicePolicies WriteProtect = 1`.
  - *Whitelist Strict*: Doar mediile amprentate în baza de date cu status `AutorizatRw` sau `AutorizatRo` sunt permise.
  - *Plafon Hard de Clasificare*: Nu se permite înregistrarea unui transfer cu nivel de secretizare mai mare decât plafonul maxim alocat mediului fizic.

---

## 4. Analiza Amenințărilor (Threat Boundaries)
- **Amenințare BadUSB / Spoofing de serie**: Un atacator cu hardware dedicat poate emula un serial cunoscut. Aplicația atenuează acest risc prin legarea amprentei de un tuplu complet `(VID, PID, Serial, Model, Capacitate, VolumeGuid)` și prin obligativitatea controlului fizic de acces.
- **Amenințare Atac Rollback DB**: Se stochează periodic starea capului de lanț (`anchor.bin`) pentru detectarea restaurării unei baze de date anterioare.

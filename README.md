# 🛡️ Registru Militar de Transferuri & Device Control v5.4
### Aplicație Desktop Air-Gapped pentru Evidența Transferurilor de Date Clasificate & Controlul Mediilor de Stocare
**Stack Tehnologic:** C# WPF, .NET 10 LTS, Clean Architecture, SQLite WAL / SQLCipher, QuestPDF, YARA/DFIR Engine.  
**Conformitate Normativă:** HG 585/2002, Legea 182/2002, NATO AC/35-D/1022, Decizia Consiliului 2013/488/UE, NIST SP 800-88r2, IEEE 2883-2022.

---

## 🚀 Pilonii Arhitecturii v5.4

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│             SISTEM MILITAR DE TRANSFERURI & DEVICE CONTROL v5.4                  │
├───────────────────────┬───────────────────────────┬──────────────────────────────┤
│ 🎨 Obsidian Tactical  │ 🛡️ Endpoint Protection    │ 🔬 Inspecție DFIR & DLP      │
│ Temă WCAG AA Dark,    │ Politici USB (BlockAll,   │ Magic Bytes (MZ/ELF blocker),│
│ Scrollbar 6px sleek,  │ ReadOnly, WhitelistOnly), │ YARA Offline Heuristics,     │
│ Cascadia Mono hashes. │ Ejectare forțată medii.   │ Zip-Slip & Script Blocker.   │
├───────────────────────┼───────────────────────────┼──────────────────────────────┤
│ ✍️ Semnare Digitală   │ 🧹 Sanitizare NIST r2     │ 🧠 Seif Cognitiv Sidecar     │
│ PAdES-LTA cu certuri  │ Suprascriere multi-pass & │ Conexiune 127.0.0.1:8765 cu  │
│ X.509 și Four-Eyes    │ eșantionare 10%, export   │ AI Memory Vault pentru       │
│ HMAC-SHA256 non-rep.  │ PDF certificat NIST/IEEE. │ proceduri și regulamente.    │
└───────────────────────┴───────────────────────────┴──────────────────────────────┘
```

---

## 📋 Cele 7 Module ale Sistemului

1. **Registru Transferuri**:
   - Vizualizare tabulară virtualizată (40px row-height), filtre dinamice pe clasificare (Neclasificat → Strict Secret SSID).
   - Exporturi rapide (CSV UTF-8, Raport HTML militar).
   - Panou lateral de inspecție detaliată a fiecărui transfer.
2. **Înregistrare Transfer (Wizard în 4 Pași)**:
   - *Pasul 1: Număr Înregistrare & Suport Fizic*: Selecție mediu fizic conectat live.
   - *Pasul 2: Flux & Entități*: Unitate sursă/destinație, persoane responsabile, curier militar.
   - *Pasul 3: Pachet Date & Inspecție DLP / DFIR*: Calcul progresiv hash SHA-256, autocompletare euristică a numărului de înregistrare conform HG 585 (`FileNameRegistryParser.cs`).
   - *Pasul 4: Validare Plafon & Semnare Four-Eyes*: Verificare HARD a plafonului de securitate al mediului și autorizare duală criptografică HMAC-SHA256.
3. **Control Medii & Whitelist (P16–P18 Forensics)**:
   - Telemetrie hardware imutabilă (VID, PID, Serie Firmware S/N, Capacitate).
   - Suport unificat pentru toate tipurile de medii: **USB, SSD/HDD SATA, NVMe M.2, Carduri SD, CD/DVD/Blu-ray**.
   - Panou de politici Endpoint Protection cu selector `Whitelist Strict`, `Doar-Citire`, `Blocare Totală USB` și `Eliminare Toate Politicile`.
4. **Seif Cognitiv & Oracol INFOSEC**:
   - Split-view dedicat: Terminal Asistent INFOSEC (60%) + Inspector Proceduri & Standarde Militare (40%).
   - Punte securizată sidecar pe loopback `127.0.0.1:8765`.
5. **Statistici & Conformitate**:
   - 4 carduri KPI de 28px cu sparklines native.
   - Sumar al volumelor de date transferate și defalcare pe niveluri de clasificare.
6. **Jurnal Audit Criptografic SHA-256**:
   - Blockchain local tamper-evident cu verificare instantanee de integritate.
   - Card dedicat pentru verificarea Blocului Genesis și detecție tentative de rollback.
7. **Gestiune Operatori & Sistem**:
   - Management operatori cu roluri administrative și clearance militar HG 585.
   - Hash-uri PIN derivate prin **Argon2id** (64 MB memorie, 3 iterații).

---

## 🛠️ Ghid de Compilare și Rulare

### Rulare în mediul de dezvoltare:
```powershell
dotnet restore
dotnet build -c Release
dotnet test
dotnet run --project src/RegistruTransferuri
```

### Publicare Pachet Standalone (Air-Gapped Single-File):
```powershell
dotnet publish src/RegistruTransferuri/RegistruTransferuri.csproj `
  -c Release `
  -r win-x64 `
  --self-contained true `
  -p:PublishSingleFile=true `
  -o bin/Publish/
```
Executabilul rezultat `bin/Publish/RegistruTransferuri.exe` (141 MB) conține toate bibliotecile necesare (runtime .NET 10, SQLCipher, QuestPDF) și poate fi copiat direct pe orice stație Windows 10/11 fără cerințe de instalare anterioară.

---

## 🧪 Testare Automată
Proiectul include o suită completă de **16 teste automate unitare** pe .NET 10 LTS:
```powershell
dotnet test RegistruTransferuri.sln
```
*Rezultat: 16 Passed, 0 Failed (100% GREEN).*

---

## 📜 Licență și Conformitate
Dezvoltat în conformitate strictă cu standardele naționale și aliate de protecție a informațiilor clasificate:
- **HG 585/2002** (Art. 41 & 60 & 65)
- **NATO AC/35-D/1022**
- **EUCI 2013/488/UE**
- **NIST SP 800-88 Rev. 2 & IEEE 2883-2022**

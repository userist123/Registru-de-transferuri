# Registru Transferuri Media v3.1 — C# / .NET 8

Rescriere completa din Python/PyQt6 (v3.0) in **C# / WPF / .NET 8**, conform documentului de arhitectura de securitate. Aplicatie desktop air-gapped pentru evidenta transferurilor pe medii de stocare clasificate.

## Cadru normativ

- **HG 585/2002** — Standarde nationale de protectie a informatiilor clasificate (Art. 41: prefixe 000/00/0/S)
- **Legea 182/2002** — Protectia informatiilor clasificate
- **Decizia Consiliului 2013/488/UE** — echivalenta EUCI (EU TOP SECRET ... EU RESTRICTED)
- **eIDAS 2.0 (UE 2024/1183)** — PAdES-B-LTA (ETSI EN 319 142), marca temporala RFC 3161, Art. 41
- **NIST SP 800-88 Rev. 2** (sept. 2025) — sanitizare Clear/Purge/Destroy; Rev. 1 retrasa la 26.09.2025
- **NIST SP 800-92** — integritatea jurnalelor de audit (tamper-evident)
- **ISO/IEC 27001:2022** — Control A.8.10 (Information Deletion)
- **Ordinul ORNISS 475/2005** — incaperi speciale de securitate, regim air-gapped

## Pilonii de securitate implementati

| Componenta | Implementare v3.1 |
|---|---|
| Baza de date | **SQLCipher AES-256-CBC**, `kdf_iter=256000`, `cipher_page_size=4096` |
| Cheie master | **DPAPI** `ProtectedData.Protect` cu `DataProtectionScope.LocalMachine` |
| Memorie volatila | `SecureBuffer` — pinned arrays + `CryptographicOperations.ZeroMemory` |
| Autentificare | PIN **PBKDF2-HMAC-SHA256** (210k iteratii, salt 16 octeti, FixedTimeEquals) + punct PKCS#11 (QSCD) |
| Audit | **Hash chain** SHA-256 + **Arbori Merkle** pentru verificare O(log n) |
| Inventar USB | **WMI** `Win32_DiskDrive` (USB) — serie hardware reala, VID/PID, litera; `UsbWatcher` |
| Auto-lock | Monitor `CardRemoved` (WinRT) — logout instant + ZeroMemory + lock overlay |
| Sanitizare | **NIST SP 800-88r2**: Clear (NC) / Purge + Crypto Erase SED (SSv) / Destroy DIN 66399 H-5 (S/SS/SSID); blocare in lant; four-eyes pentru SS/SSID |
| Export | PDF (QuestPDF) + punct PAdES-B-LTA (BouncyCastle/iText7) cu DTS RFC 3161; CSV UTF-8 |
| Need-to-Know | Filtrare UI + blocare la inregistrare peste `MaxClearance` |

## Build si rulare

```bash
dotnet restore
dotnet build -c Release
dotnet test
dotnet run --project src/RegistruTransferuri
```

Cerinte: .NET 8 SDK, Windows 10/11.

## Puncte de integrare ramase (marcate in cod)

1. **Pkcs11Interop** — apeluri reale C_Login/C_Sign in `SmartCardSession`.
2. **PAdES-LTA** — `PadesExportService.ApplyPadesLtaSeal`: BouncyCastle PdfSigner + TSAClient RFC 3161 + embed OCSP/CRL.
3. **Cryptographic Erase SED** — `SanitizationService.CryptographicEraseSed`: DeviceIoControl.
4. **CardRemoved WinRT** — `SmartCardRemovalMonitor.StartMonitoring`.

# Registru Transferuri Media v3.0 (Air-Gapped & Security Edition)

Aplicație desktop specializată în evidența, auditul și trasabilitatea transferurilor de date pe medii de stocare amovibile în medii cu cerințe stricte de securitate și conformitate militară/guvernamentală.

## Cadrul Normativ & Conformitate Legală
- **HG 585/2002** — Standardele naționale de protecție a informațiilor clasificate în România (Art. 41, 60–65, 73).
- **Legea 182/2002** — Protecția informațiilor secrete de stat și secrete de serviciu.
- **HG 781/2002** — Protecția informațiilor secrete de serviciu.
- **NIST SP 800-88 Rev. 1** — Guidelines for Media Sanitization (Clear, Purge, Destroy).
- **ISO/IEC 27001:2022** — Controlul A.8.10 (Information Deletion) și A.8.14 (Redundancy).

## Arhitectură & Module v3.0
1. **Autentificare & Control Acces**: Login cu PIN criptat (SHA-256 + Salt) și roluri granulare (Admin, Ofițer Securitate, Operator).
2. **Numerotare Conformă**: Prefixare automată în funcție de clasificare (`000` SSID, `00` SS, `0` Secret, `S` Secret de Serviciu, `NC` Neclasificat).
3. **Integritate Criptografică**: Hash canonic complet SHA-256 pentru fiecare înregistrare și Jurnal de Audit bazat pe lanț de hash-uri (Tamper-Evident Hash Chain).
4. **Inventar Medii Amovibile**: Evidența seriilor hardware (S/N), a stării fizice și a proceselor de casare/sanitarizare.
5. **Rapoarte & Export**: Export CSV și Rapoarte Registru HTML pregătite pentru tipar și semnare olografă/PDF.

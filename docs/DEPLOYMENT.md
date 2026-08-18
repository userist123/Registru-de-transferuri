# GHID DE DEPLOYMENT & HARDENING STAȚIE AIR-GAPPED

## 1. Compilare & Publicare Self-Contained pe .NET 10 LTS

Pentru o stație militară strict deconectată de la rețea (Air-Gapped), aplicația trebuie publicată self-contained pe arhitectura x64:

```powershell
dotnet publish src/RegistruTransferuri/RegistruTransferuri.csproj `
  -c Release `
  -r win-x64 `
  --self-contained true `
  -p:PublishSingleFile=true `
  -p:IncludeNativeLibrariesForSelfExtract=true `
  -o bin/Publish/
```

---

## 2. Semnare Digitală Authenticode (Opțional / Recomandat)

Dacă stația dispune de certificat de semnare cod emis de PKI-ul militar intern:

```powershell
SignTool sign /fd SHA256 /a /tr http://timestamp.server /td SHA256 "bin/Publish/RegistruTransferuri.exe"
```

---

## 3. Politică de Control al Execuției (AppLocker / Windows Defender Application Control)

Pentru asigurarea integrității, se recomandă restricționarea rulării exclusiv pentru binarele semnate sau amplasate în folderul protejat:

```xml
<AppLockerPolicy Version="1">
  <RuleCollection Type="Exe" EnforcementMode="Enabled">
    <FileHashRule Id="d1887e5b-1194-4d2a-883a-18b82e5d9c22" Name="Permite Registru Transferuri" Action="Allow">
      <Conditions>
        <FileHashCondition>
          <FileHash Type="SHA256" Data="[HASH_PRODUS]" SourceFileName="RegistruTransferuri.exe" SourceFileLength="[SIZE]" />
        </FileHashCondition>
      </Conditions>
    </FileHashRule>
  </RuleCollection>
</AppLockerPolicy>
```

---

## 4. Drepturi Administrative & Permisiuni de Sistem

- **Drepturi Administrative Locale**: Necesar doar pentru comutarea politicilor globale de porturi `USBSTOR` (`HKLM\SYSTEM\CurrentControlSet\Services\USBSTOR`) și `WriteProtect`. În mod normal de utilizator, aplicația rulează în spațiul propriu cu drepturi standard de acces la baza SQLite criptată.

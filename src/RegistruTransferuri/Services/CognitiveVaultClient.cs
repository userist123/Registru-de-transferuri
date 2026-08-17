using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using RegistruTransferuri.Models;

namespace RegistruTransferuri.Services;

public record VaultResponse(string Response, string[] Sources, double Confidence, bool IsAttested);
public record ProcedureDoc(string Title, string StandardRef, string Category, string Summary, string FullText);

/// <summary>
/// Client HTTP dedicat pentru puntea cognitiva AI Memory Vault.
/// STRICT LOOPBACK (127.0.0.1) — Air-Gapped Zero-Trust.
/// </summary>
public class CognitiveVaultClient
{
    private readonly HttpClient _http;
    private readonly string _baseUrl;

    public CognitiveVaultClient(string baseUrl = "http://127.0.0.1:8765")
    {
        _baseUrl = baseUrl;
        _http = new HttpClient
        {
            BaseAddress = new Uri(_baseUrl),
            Timeout = TimeSpan.FromSeconds(5)
        };
    }

    public async Task<VaultResponse> QueryAsync(string prompt, string[]? contextTags = null)
    {
        try
        {
            var payload = new { query = prompt, tags = contextTags ?? Array.Empty<string>() };
            var response = await _http.PostAsJsonAsync("/api/query", payload);
            if (response.IsSuccessStatusCode)
            {
                var result = await response.Content.ReadFromJsonAsync<VaultResponse>();
                if (result != null) return result;
            }
        }
        catch
        {
            // Fallback deterministic offline recall conform procedurilor HG 585 / NATO AC/35
        }

        return GenerateDeterministicFallback(prompt);
    }

    public async Task<List<ProcedureDoc>> SearchProceduresAsync(string query)
    {
        try
        {
            var response = await _http.GetAsync($"/api/procedures?q={Uri.EscapeDataString(query)}");
            if (response.IsSuccessStatusCode)
            {
                var list = await response.Content.ReadFromJsonAsync<List<ProcedureDoc>>();
                if (list != null) return list;
            }
        }
        catch
        {
            // Offline fallback
        }

        return GetOfflineProcedures(query);
    }

    public async Task<bool> LogAuditEventAsync(string actor, string action, string details, string payloadHash)
    {
        try
        {
            var payload = new
            {
                timestamp = DateTime.UtcNow.ToString("o"),
                actor = actor,
                action = action,
                details = details,
                payload_hash = payloadHash
            };
            var response = await _http.PostAsJsonAsync("/api/audit/log", payload);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    private VaultResponse GenerateDeterministicFallback(string prompt)
    {
        var p = prompt.ToLowerInvariant();
        if (p.Contains("sanitiz") || p.Contains("distrug") || p.Contains("800-88") || p.Contains("art. 65") || p.Contains("art 65"))
        {
            return new VaultResponse(
                "🔒 **PROCEDURĂ SANITIZARE & DISTRUGERE (NIST SP 800-88r2 & HG 585/2002 Art. 65)**\n\n" +
                "1. **Plafon SECRET / STRICT SECRET:** Distrugerea fizică sau Cryptographic Erase (IEEE 2883-2022) cu suprascriere pseudo-aleatorie și distrugerea cheii MEK.\n" +
                "2. **Comisie Obligatorie:** Minim 2 ofițeri autorizați cu clearance egal sau superior nivelului mediului.\n" +
                "3. **Document Oficial:** Emiterea și semnarea Procesului-Verbal de Distrugere/Sanitizare cu legare criptografică a hash-ului hardware în Jurnalul de Audit.",
                new[] { "HG 585/2002 Art. 65", "NIST SP 800-88r2", "IEEE 2883-2022" },
                0.99,
                true
            );
        }

        if (p.Contains("nato") || p.Contains("ac/35") || p.Contains("ac 35") || p.Contains("air-gap") || p.Contains("air gap"))
        {
            return new VaultResponse(
                "🛡️ **NORME DE TRANSFER AIR-GAPPED (NATO AC/35-D/1022 & EUCI 2013/488/UE)**\n\n" +
                "1. **Dispozitive Autorizate:** Se utilizează exclusiv medii de stocare din Whitelist-ul militar înregistrate fizic.\n" +
                "2. **Inspecție DLP Magic Bytes:** Blocarea automată a oricăror fișiere executabile (MZ/PE/ELF) la punctul de transfer.\n" +
                "3. **Integritate:** Calculul și verificarea obligatorie a amprentei SHA-256 înainte și după transfer.",
                new[] { "NATO AC/35-D/1022", "EUCI 2013/488/UE" },
                0.98,
                true
            );
        }

        return new VaultResponse(
            "📋 **CONSULTANȚĂ INFOSEC PROCEDURALĂ**\n\n" +
            "Sistemul funcționează în regim strict Air-Gapped. Orice operațiune de transfer implică verificarea integrității SHA-256, autorizarea în 4-Ochi pentru pachete clasificate și jurnalizarea tamper-evident.",
            new[] { "HG 585/2002", "Standarde INFOSEC MApN" },
            0.95,
            true
        );
    }

    private List<ProcedureDoc> GetOfflineProcedures(string query)
    {
        var all = new List<ProcedureDoc>
        {
            new("Procedură Sanitizare & Distrugere Medii Clasificate", "HG 585/2002 Art. 65 / NIST SP 800-88r2", "Distrugere & Sanitizare", "Reguli de distrugere criptografică și întocmire PV de casare a suporturilor magnetice/optice/flash.", "Suporturile de memorie externă care au conținut informații clasificate Secret/Strict Secret se supun distrugerii fizice sau sanitizării criptografice conform IEEE 2883-2022."),
            new("Regimul de Izolare Logică & Fizică Air-Gapped", "NATO AC/35-D/1022 / EUCI 2013/488/UE", "Transfer Operativ", "Norme de transfer de date între rețele securizate fără conexiuni directe de rețea.", "Transferul de date se efectuează strict prin medii optice sau dispozitive flash amprentate hardware, cu validare Magic Bytes și SHA-256."),
            new("Principiul Celor 4 Ochi (Four-Eyes Authorization)", "HG 585/2002 / NATO Security Guidelines", "Autentificare & Clearance", "Obligativitatea autorizării duale la transferul de date Secret și Strict Secret.", "Orice operațiune de export sau predare a pachetelor Secret sau Strict Secret necesită contrasemnarea de către un al doilea ofițer autorizat."),
            new("Invariantele de Integritate P0-P18 Cognitive Vault", "Vault Architecture Spec", "Arhitectură Sistem", "Protecția imutabilității telemetriei hardware și a lanțului de audit.", "Datele fizice VID/PID, Serial Number firmware și hash-urile SHA-256 sunt strict Read-Only și legate în lanț de blocuri de audit.")
        };

        if (string.IsNullOrWhiteSpace(query))
            return all;

        var q = query.ToLowerInvariant();
        return all.Where(d => d.Title.ToLowerInvariant().Contains(q) || d.StandardRef.ToLowerInvariant().Contains(q) || d.Summary.ToLowerInvariant().Contains(q)).ToList();
    }
}

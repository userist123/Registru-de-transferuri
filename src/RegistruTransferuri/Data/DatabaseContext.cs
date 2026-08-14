using Microsoft.Data.Sqlite;
using RegistruTransferuri.Models;
using RegistruTransferuri.Security;

namespace RegistruTransferuri.Data;

/// <summary>
/// Context baza de date SQLCipher — AES-256-CBC transparent, cheie livrata ca byte literal.
/// PRAGMA kdf_iter = 256000 (PBKDF2 hardening), cipher_page_size = 4096 (aliniere SSD).
/// Cheia master este protejata prin DPAPI LocalMachine — vezi DpapiKeyProtector.
/// </summary>
public sealed class DatabaseContext : IDisposable
{
    private readonly SqliteConnection _conn;
    private readonly SecureBuffer _keyBuffer;

    public DatabaseContext(string dbPath, SecureBuffer keyBuffer)
    {
        _keyBuffer = keyBuffer;
        SQLitePCL.Batteries_V2.Init();

        var hexKey = Convert.ToHexString(_keyBuffer.Span);
        var csb = new SqliteConnectionStringBuilder
        {
            DataSource = dbPath,
            Mode = SqliteOpenMode.ReadWriteCreate,
            Password = hexKey
        };
        _conn = new SqliteConnection(csb.ConnectionString);
        _conn.Open();

        using var cmd = _conn.CreateCommand();
        cmd.CommandText = @"
            PRAGMA kdf_iter = 256000;
            PRAGMA cipher_page_size = 4096;
            PRAGMA journal_mode = WAL;
            PRAGMA foreign_keys = ON;";
        cmd.ExecuteNonQuery();

        InitializeSchema();
    }

    private void InitializeSchema()
    {
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = @"
        CREATE TABLE IF NOT EXISTS operators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Operator',
            max_clearance INTEGER NOT NULL DEFAULT 0,
            pin_salt BLOB NOT NULL,
            pin_hash BLOB NOT NULL,
            smartcard_dn TEXT,
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registry_number TEXT NOT NULL UNIQUE,
            classification INTEGER NOT NULL,
            transfer_date_utc TEXT NOT NULL,
            source_institution TEXT NOT NULL,
            destination_institution TEXT NOT NULL,
            source_person TEXT NOT NULL,
            destination_person TEXT NOT NULL,
            media_type TEXT NOT NULL,
            media_serial TEXT NOT NULL,
            media_inventory_code TEXT NOT NULL DEFAULT '',
            content_description TEXT NOT NULL DEFAULT '',
            operator_username TEXT NOT NULL,
            signed INTEGER NOT NULL DEFAULT 0,
            signed_at_utc TEXT,
            signed_by TEXT,
            cancelled INTEGER NOT NULL DEFAULT 0,
            cancellation_reason TEXT,
            integrity_hash TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_transfers_class ON transfers(classification);
        CREATE INDEX IF NOT EXISTS idx_transfers_date ON transfers(transfer_date_utc);
        CREATE INDEX IF NOT EXISTS idx_transfers_serial ON transfers(media_serial);
        CREATE TABLE IF NOT EXISTS media_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number TEXT NOT NULL UNIQUE,
            inventory_code TEXT NOT NULL,
            media_type TEXT NOT NULL,
            vendor_id TEXT NOT NULL DEFAULT '',
            product_id TEXT NOT NULL DEFAULT '',
            capacity_bytes INTEGER NOT NULL DEFAULT 0,
            max_classification INTEGER NOT NULL DEFAULT 0,
            physical_location TEXT NOT NULL DEFAULT '',
            status INTEGER NOT NULL DEFAULT 0,
            sanitization_method INTEGER,
            destruction_cert_number TEXT,
            sanitized_at_utc TEXT,
            sanitized_by TEXT,
            verified_by TEXT
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            sequence INTEGER PRIMARY KEY,
            timestamp_utc TEXT NOT NULL,
            action TEXT NOT NULL,
            operator_username TEXT NOT NULL,
            details TEXT NOT NULL DEFAULT '',
            previous_hash TEXT NOT NULL,
            entry_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS registry_counters (
            year INTEGER NOT NULL,
            classification INTEGER NOT NULL,
            counter INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (year, classification)
        );
        CREATE TABLE IF NOT EXISTS merkle_roots (
            date_utc TEXT PRIMARY KEY,
            root_hash TEXT NOT NULL,
            entry_count INTEGER NOT NULL
        );";
        cmd.ExecuteNonQuery();
    }

    /// <summary>
    /// Genereaza numarul de registru conform Art. 41 HG 585/2002:
    /// PREFIX-YYYY-[000|00|0|S|NC]-NNNN, contor resetat per an si per nivel.
    /// </summary>
    public string NextRegistryNumber(string institutionPrefix, ClassificationLevel level)
    {
        var year = DateTime.UtcNow.Year;
        using var tx = _conn.BeginTransaction();
        using var cmd = _conn.CreateCommand();
        cmd.Transaction = tx;
        cmd.CommandText = @"
            INSERT INTO registry_counters (year, classification, counter) VALUES ($y, $c, 1)
            ON CONFLICT(year, classification) DO UPDATE SET counter = counter + 1
            RETURNING counter;";
        cmd.Parameters.AddWithValue("$y", year);
        cmd.Parameters.AddWithValue("$c", (int)level);
        var counter = (long)(cmd.ExecuteScalar() ?? 1L);
        tx.Commit();
        return $"{institutionPrefix}-{year}-{level.RegistryPrefix()}-{counter:D4}";
    }

    public long AppendAudit(string action, string operatorUsername, string details)
    {
        using var tx = _conn.BeginTransaction();
        string prevHash = AuditChain.GenesisHash;
        long seq = 1;
        using (var read = _conn.CreateCommand())
        {
            read.Transaction = tx;
            read.CommandText = "SELECT sequence, entry_hash FROM audit_log ORDER BY sequence DESC LIMIT 1";
            using var r = read.ExecuteReader();
            if (r.Read()) { seq = r.GetInt64(0) + 1; prevHash = r.GetString(1); }
        }
        var ts = DateTime.UtcNow;
        var hash = AuditChain.ComputeEntryHash(prevHash, seq, ts, action, operatorUsername, details);
        using (var ins = _conn.CreateCommand())
        {
            ins.Transaction = tx;
            ins.CommandText = @"INSERT INTO audit_log
                (sequence, timestamp_utc, action, operator_username, details, previous_hash, entry_hash)
                VALUES ($s,$t,$a,$o,$d,$p,$h)";
            ins.Parameters.AddWithValue("$s", seq);
            ins.Parameters.AddWithValue("$t", ts.ToString("O"));
            ins.Parameters.AddWithValue("$a", action);
            ins.Parameters.AddWithValue("$o", operatorUsername);
            ins.Parameters.AddWithValue("$d", details);
            ins.Parameters.AddWithValue("$p", prevHash);
            ins.Parameters.AddWithValue("$h", hash);
            ins.ExecuteNonQuery();
        }
        tx.Commit();
        return seq;
    }

    /// <summary>Verifica lantul de audit la pornire — returneaza secventa compromisa sau -1.</summary>
    public long VerifyAuditChain()
    {
        var entries = new List<AuditEntry>();
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = @"SELECT sequence, timestamp_utc, action, operator_username, details,
                            previous_hash, entry_hash FROM audit_log ORDER BY sequence";
        using var r = cmd.ExecuteReader();
        while (r.Read())
            entries.Add(new AuditEntry(r.GetInt64(0), DateTime.Parse(r.GetString(1)),
                r.GetString(2), r.GetString(3), r.GetString(4), r.GetString(5), r.GetString(6)));
        return AuditChain.VerifyChain(entries);
    }

    public void InsertTransfer(TransferRecord t)
    {
        t.IntegrityHash = t.ComputeIntegrityHash();
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = @"INSERT INTO transfers
            (registry_number, classification, transfer_date_utc, source_institution,
             destination_institution, source_person, destination_person, media_type,
             media_serial, media_inventory_code, content_description, operator_username, integrity_hash)
            VALUES ($rn,$cl,$dt,$si,$di,$sp,$dp,$mt,$ms,$mic,$cd,$op,$ih)";
        cmd.Parameters.AddWithValue("$rn", t.RegistryNumber);
        cmd.Parameters.AddWithValue("$cl", (int)t.Classification);
        cmd.Parameters.AddWithValue("$dt", t.TransferDateUtc.ToString("O"));
        cmd.Parameters.AddWithValue("$si", t.SourceInstitution);
        cmd.Parameters.AddWithValue("$di", t.DestinationInstitution);
        cmd.Parameters.AddWithValue("$sp", t.SourcePerson);
        cmd.Parameters.AddWithValue("$dp", t.DestinationPerson);
        cmd.Parameters.AddWithValue("$mt", t.MediaType);
        cmd.Parameters.AddWithValue("$ms", t.MediaSerialNumber);
        cmd.Parameters.AddWithValue("$mic", t.MediaInventoryCode);
        cmd.Parameters.AddWithValue("$cd", t.ContentDescription);
        cmd.Parameters.AddWithValue("$op", t.OperatorUsername);
        cmd.Parameters.AddWithValue("$ih", t.IntegrityHash);
        cmd.ExecuteNonQuery();
        AppendAudit("INSERT_TRANSFER", t.OperatorUsername,
            $"nr={t.RegistryNumber}; class={t.Classification}; serial={t.MediaSerialNumber}");
    }

    public SqliteConnection RawConnection => _conn;

    public void Dispose()
    {
        _conn.Dispose();
        _keyBuffer.Dispose();
    }
}

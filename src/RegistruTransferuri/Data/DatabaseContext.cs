using System.IO;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Data.Sqlite;
using RegistruTransferuri.Models;
using RegistruTransferuri.Security;

namespace RegistruTransferuri.Data;

/// <summary>
/// Context de baza de date C# SQLite securizat cu jurnal WAL si interogari atomice.
/// </summary>
public sealed class DatabaseContext : IDisposable
{
    private readonly SqliteConnection _conn;
    public string LocalStationHost { get; }

    public DatabaseContext(string dbPath, SecureBuffer? keyBuffer = null)
    {
        LocalStationHost = Environment.MachineName.ToUpperInvariant();
        SQLitePCL.Batteries_V2.Init();

        var csb = new SqliteConnectionStringBuilder
        {
            DataSource = dbPath,
            Mode = SqliteOpenMode.ReadWriteCreate
        };

        _conn = new SqliteConnection(csb.ConnectionString);
        _conn.Open();

        using var cmd = _conn.CreateCommand();
        cmd.CommandText = @"
            PRAGMA journal_mode = WAL;
            PRAGMA foreign_keys = ON;
            PRAGMA busy_timeout = 5000;";
        cmd.ExecuteNonQuery();

        InitializeSchema();
        EnsureDefaultOperators();
    }

    public SqliteConnection RawConnection => _conn;

    private void InitializeSchema()
    {
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = @"
        CREATE TABLE IF NOT EXISTS operators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Operator',
            military_unit TEXT NOT NULL DEFAULT 'MApN / Structura Securitate',
            max_clearance INTEGER NOT NULL DEFAULT 2,
            pin_salt BLOB NOT NULL,
            pin_hash BLOB NOT NULL,
            smartcard_dn TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            last_login_utc TEXT
        );

        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registry_number TEXT NOT NULL UNIQUE,
            classification INTEGER NOT NULL,
            transfer_date_utc TEXT NOT NULL,
            direction TEXT NOT NULL DEFAULT 'iesire',
            source_institution TEXT NOT NULL,
            source_station_host TEXT NOT NULL,
            source_person TEXT NOT NULL,
            source_person_role TEXT NOT NULL DEFAULT 'Operator IT',
            source_person_id_number TEXT NOT NULL DEFAULT '',
            source_person_clearance TEXT NOT NULL DEFAULT 'Secret',
            destination_institution TEXT NOT NULL,
            destination_station_host TEXT NOT NULL DEFAULT '',
            destination_person TEXT NOT NULL,
            courier_name TEXT,
            courier_permit_number TEXT,
            media_type TEXT NOT NULL,
            media_serial TEXT NOT NULL,
            media_vendor_id TEXT NOT NULL DEFAULT '',
            media_product_id TEXT NOT NULL DEFAULT '',
            media_inventory_code TEXT NOT NULL DEFAULT '',
            media_friendly_label TEXT NOT NULL DEFAULT '',
            storage_medium_id INTEGER,
            payload_file_name TEXT NOT NULL DEFAULT '',
            payload_type TEXT NOT NULL DEFAULT 'Arhiva Securizata',
            payload_size_gb REAL NOT NULL DEFAULT 0.0,
            payload_files_count INTEGER NOT NULL DEFAULT 1,
            payload_sha256_hash TEXT NOT NULL DEFAULT '',
            content_description TEXT NOT NULL DEFAULT '',
            antivirus_scanned INTEGER NOT NULL DEFAULT 1,
            antivirus_details TEXT NOT NULL DEFAULT '',
            legal_base TEXT NOT NULL DEFAULT 'HG 585/2002 Art. 60-73',
            approval_order_number TEXT,
            dissemination_restrictions TEXT,
            notes TEXT,
            operator_username TEXT NOT NULL,
            signed INTEGER NOT NULL DEFAULT 0,
            signed_at_utc TEXT,
            signed_by TEXT,
            four_eyes_approver_name TEXT,
            four_eyes_approver_role TEXT,
            four_eyes_approved_at_utc TEXT,
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
            friendly_name TEXT NOT NULL DEFAULT '',
            media_type TEXT NOT NULL,
            vendor_id TEXT NOT NULL DEFAULT '',
            product_id TEXT NOT NULL DEFAULT '',
            manufacturer TEXT NOT NULL DEFAULT '',
            model TEXT NOT NULL DEFAULT '',
            capacity_bytes INTEGER NOT NULL DEFAULT 0,
            max_classification INTEGER NOT NULL DEFAULT 2,
            status INTEGER NOT NULL DEFAULT 0,
            encryption_status TEXT NOT NULL DEFAULT 'BitLocker To Go (AES-256)',
            custodian_name TEXT NOT NULL DEFAULT '',
            custodian_unit TEXT NOT NULL DEFAULT 'MApN / Structura Securitate',
            notes TEXT,
            date_enrolled_utc TEXT NOT NULL,
            sanitization_method INTEGER,
            destruction_cert_number TEXT,
            sanitized_at_utc TEXT,
            sanitized_by TEXT,
            verified_by TEXT
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc TEXT NOT NULL,
            action TEXT NOT NULL,
            operator_username TEXT NOT NULL,
            details TEXT,
            entity_id TEXT,
            previous_hash TEXT NOT NULL,
            entry_hash TEXT NOT NULL
        );
        ";
        cmd.ExecuteNonQuery();
    }

    private void EnsureDefaultOperators()
    {
        using var countCmd = _conn.CreateCommand();
        countCmd.CommandText = "SELECT COUNT(*) FROM operators";
        var count = Convert.ToInt32(countCmd.ExecuteScalar());
        if (count == 0)
        {
            var (hAdmin, sAdmin) = HashPin("123456");
            AddOperatorDirect("admin", "Administrator Sistem (Ofițer Securitate)", "admin", "MApN / Baza Tehnologică Centrală", ClassificationLevel.StrictSecretDeImportantaDeosebita, hAdmin, sAdmin);

            var (hOp, sOp) = HashPin("111111");
            AddOperatorDirect("operator1", "Cpt. Ionescu Radu", "operator", "MApN / Structura Securitate", ClassificationLevel.Secret, hOp, sOp);
        }
    }

    private void AddOperatorDirect(string username, string fullName, string role, string unit, ClassificationLevel maxClf, byte[] hash, byte[] salt)
    {
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = @"INSERT INTO operators (username, full_name, role, military_unit, max_clearance, pin_salt, pin_hash, active)
                            VALUES (@u, @f, @r, @m, @c, @s, @h, 1)";
        cmd.Parameters.AddWithValue("@u", username);
        cmd.Parameters.AddWithValue("@f", fullName);
        cmd.Parameters.AddWithValue("@r", role);
        cmd.Parameters.AddWithValue("@m", unit);
        cmd.Parameters.AddWithValue("@c", (int)maxClf);
        cmd.Parameters.AddWithValue("@s", salt);
        cmd.Parameters.AddWithValue("@h", hash);
        cmd.ExecuteNonQuery();
    }

    public static (byte[] Hash, byte[] Salt) HashPin(string pin)
    {
        return PinHasher.HashPin(pin);
    }

    public static bool VerifyPin(string pin, byte[] storedHash, byte[] storedSalt)
    {
        // 1. Incearca mai intai verificarea Argon2id (modern)
        if (PinHasher.VerifyPin(pin, storedHash, storedSalt))
            return true;

        // 2. Fallback / Migrare transparenta pentru hash-uri vechi PBKDF2 (100k iteratii)
        try
        {
            var testHash = Rfc2898DeriveBytes.Pbkdf2(pin, storedSalt, 100_000, HashAlgorithmName.SHA256, 32);
            return CryptographicOperations.FixedTimeEquals(testHash, storedHash);
        }
        catch
        {
            return false;
        }
    }

    public List<Operator> GetActiveOperators()
    {
        var list = new List<Operator>();
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = "SELECT id, username, full_name, role, military_unit, max_clearance, pin_salt, pin_hash, active FROM operators WHERE active=1 ORDER BY full_name ASC";
        using var r = cmd.ExecuteReader();
        while (r.Read())
        {
            list.Add(new Operator
            {
                Id = r.GetInt32(0),
                Username = r.GetString(1),
                FullName = r.GetString(2),
                Role = r.GetString(3),
                MilitaryUnit = r.GetString(4),
                MaxClearance = (ClassificationLevel)r.GetInt32(5),
                PinSalt = (byte[])r[6],
                PinHash = (byte[])r[7],
                Active = r.GetInt32(8) == 1
            });
        }
        return list;
    }

    public Operator? Authenticate(int operatorId, string pin)
    {
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = "SELECT id, username, full_name, role, military_unit, max_clearance, pin_salt, pin_hash, active FROM operators WHERE id=@id AND active=1";
        cmd.Parameters.AddWithValue("@id", operatorId);
        using var r = cmd.ExecuteReader();
        if (r.Read())
        {
            var op = new Operator
            {
                Id = r.GetInt32(0),
                Username = r.GetString(1),
                FullName = r.GetString(2),
                Role = r.GetString(3),
                MilitaryUnit = r.GetString(4),
                MaxClearance = (ClassificationLevel)r.GetInt32(5),
                PinSalt = (byte[])r[6],
                PinHash = (byte[])r[7],
                Active = r.GetInt32(8) == 1
            };
            if (VerifyPin(pin, op.PinHash, op.PinSalt))
            {
                AppendAudit("LOGIN_SUCCESS", op.Username, $"Autentificare reusita pentru {op.FullName}");
                return op;
            }
            AppendAudit("LOGIN_FAILED", op.Username, $"Incercare esuata PIN pentru {op.FullName}");
        }
        return null;
    }

    public string NextRegistryNumber(string prefix = "MAPN", ClassificationLevel level = ClassificationLevel.Neclasificat)
    {
        var year = DateTime.UtcNow.Year;
        var pfx = level.GetPrefix();
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = "SELECT COUNT(*) FROM transfers WHERE transfer_date_utc LIKE @y";
        cmd.Parameters.AddWithValue("@y", $"{year}%");
        var count = Convert.ToInt32(cmd.ExecuteScalar()) + 1;
        return $"{prefix}-{year}-{pfx}-{count:D4}";
    }

    public void InsertTransfer(TransferRecord tx)
    {
        tx.IntegrityHash = ComputeTransferHash(tx);
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = @"INSERT INTO transfers (
            registry_number, classification, transfer_date_utc, direction,
            source_institution, source_station_host, source_person, source_person_role, source_person_id_number, source_person_clearance,
            destination_institution, destination_station_host, destination_person,
            courier_name, courier_permit_number,
            media_type, media_serial, media_vendor_id, media_product_id, media_inventory_code, media_friendly_label, storage_medium_id,
            payload_file_name, payload_type, payload_size_gb, payload_files_count, payload_sha256_hash,
            content_description, antivirus_scanned, antivirus_details,
            legal_base, approval_order_number, dissemination_restrictions, notes,
            operator_username, signed, signed_at_utc, signed_by,
            four_eyes_approver_name, four_eyes_approver_role, four_eyes_approved_at_utc,
            cancelled, integrity_hash
        ) VALUES (
            @nr, @clf, @dt, @dir,
            @sinst, @shost, @spers, @srole, @sid, @sclear,
            @dinst, @dhost, @dpers,
            @cname, @cperm,
            @mtip, @msn, @mvid, @mpid, @minv, @mlbl, @smid,
            @pfile, @ptip, @psize, @pcount, @phash,
            @desc, @avscan, @avdet,
            @lbase, @appord, @dissres, @notes,
            @op, @sgn, @sgnat, @sgnby,
            @f4name, @f4role, @f4at,
            @cnc, @inhash
        )";

        cmd.Parameters.AddWithValue("@nr", tx.RegistryNumber);
        cmd.Parameters.AddWithValue("@clf", (int)tx.Classification);
        cmd.Parameters.AddWithValue("@dt", tx.TransferDateUtc.ToString("o"));
        cmd.Parameters.AddWithValue("@dir", tx.Direction);
        cmd.Parameters.AddWithValue("@sinst", tx.SourceInstitution);
        cmd.Parameters.AddWithValue("@shost", tx.SourceStationHost);
        cmd.Parameters.AddWithValue("@spers", tx.SourcePerson);
        cmd.Parameters.AddWithValue("@srole", tx.SourcePersonRole);
        cmd.Parameters.AddWithValue("@sid", tx.SourcePersonIdNumber);
        cmd.Parameters.AddWithValue("@sclear", tx.SourcePersonClearance);
        cmd.Parameters.AddWithValue("@dinst", tx.DestinationInstitution);
        cmd.Parameters.AddWithValue("@dhost", tx.DestinationStationHost);
        cmd.Parameters.AddWithValue("@dpers", tx.DestinationPerson);
        cmd.Parameters.AddWithValue("@cname", (object?)tx.CourierName ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@cperm", (object?)tx.CourierPermitNumber ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@mtip", tx.MediaType);
        cmd.Parameters.AddWithValue("@msn", tx.MediaSerialNumber);
        cmd.Parameters.AddWithValue("@mvid", tx.MediaVendorId);
        cmd.Parameters.AddWithValue("@mpid", tx.MediaProductId);
        cmd.Parameters.AddWithValue("@minv", tx.MediaInventoryCode);
        cmd.Parameters.AddWithValue("@mlbl", tx.MediaFriendlyLabel);
        cmd.Parameters.AddWithValue("@smid", (object?)tx.StorageMediumId ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@pfile", tx.PayloadFileName);
        cmd.Parameters.AddWithValue("@ptip", tx.PayloadType);
        cmd.Parameters.AddWithValue("@psize", tx.PayloadSizeGb);
        cmd.Parameters.AddWithValue("@pcount", tx.PayloadFilesCount);
        cmd.Parameters.AddWithValue("@phash", tx.PayloadSha256Hash);
        cmd.Parameters.AddWithValue("@desc", tx.ContentDescription);
        cmd.Parameters.AddWithValue("@avscan", tx.AntivirusScanned ? 1 : 0);
        cmd.Parameters.AddWithValue("@avdet", tx.AntivirusDetails);
        cmd.Parameters.AddWithValue("@lbase", tx.LegalBase);
        cmd.Parameters.AddWithValue("@appord", (object?)tx.ApprovalOrderNumber ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@dissres", (object?)tx.DisseminationRestrictions ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@notes", (object?)tx.Notes ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@op", tx.OperatorUsername);
        cmd.Parameters.AddWithValue("@sgn", tx.Signed ? 1 : 0);
        cmd.Parameters.AddWithValue("@sgnat", tx.SignedAtUtc.HasValue ? (object)tx.SignedAtUtc.Value.ToString("o") : DBNull.Value);
        cmd.Parameters.AddWithValue("@sgnby", (object?)tx.SignedBy ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@f4name", (object?)tx.FourEyesApproverName ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@f4role", (object?)tx.FourEyesApproverRole ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@f4at", tx.FourEyesApprovedAtUtc.HasValue ? (object)tx.FourEyesApprovedAtUtc.Value.ToString("o") : DBNull.Value);
        cmd.Parameters.AddWithValue("@cnc", tx.Cancelled ? 1 : 0);
        cmd.Parameters.AddWithValue("@inhash", tx.IntegrityHash);
        cmd.ExecuteNonQuery();

        AppendAudit("CREATE_TRANSFER", tx.OperatorUsername, $"Inregistrat transfer militar {tx.RegistryNumber} [{tx.Classification.ToDisplayName()}]", tx.RegistryNumber);
    }

    public List<TransferRecord> GetTransfers(string? search = null, ClassificationLevel? clf = null)
    {
        var list = new List<TransferRecord>();
        var query = "SELECT * FROM transfers WHERE 1=1";
        if (clf.HasValue) query += " AND classification = " + (int)clf.Value;
        if (!string.IsNullOrWhiteSpace(search))
        {
            query += " AND (registry_number LIKE @s OR source_institution LIKE @s OR destination_institution LIKE @s OR source_person LIKE @s OR media_serial LIKE @s OR media_friendly_label LIKE @s OR payload_file_name LIKE @s)";
        }
        query += " ORDER BY transfer_date_utc DESC LIMIT 500";

        using var cmd = _conn.CreateCommand();
        cmd.CommandText = query;
        if (!string.IsNullOrWhiteSpace(search)) cmd.Parameters.AddWithValue("@s", $"%{search}%");

        using var r = cmd.ExecuteReader();
        while (r.Read())
        {
            list.Add(ReadTransfer(r));
        }
        return list;
    }

    private static TransferRecord ReadTransfer(SqliteDataReader r)
    {
        return new TransferRecord
        {
            Id = Convert.ToInt32(r["id"]),
            RegistryNumber = Convert.ToString(r["registry_number"]) ?? "",
            Classification = (ClassificationLevel)Convert.ToInt32(r["classification"]),
            TransferDateUtc = DateTime.Parse(Convert.ToString(r["transfer_date_utc"]) ?? DateTime.UtcNow.ToString("o")),
            Direction = Convert.ToString(r["direction"]) ?? "iesire",
            SourceInstitution = Convert.ToString(r["source_institution"]) ?? "",
            SourceStationHost = Convert.ToString(r["source_station_host"]) ?? "",
            SourcePerson = Convert.ToString(r["source_person"]) ?? "",
            SourcePersonRole = Convert.ToString(r["source_person_role"]) ?? "",
            SourcePersonIdNumber = Convert.ToString(r["source_person_id_number"]) ?? "",
            SourcePersonClearance = Convert.ToString(r["source_person_clearance"]) ?? "Secret",
            DestinationInstitution = Convert.ToString(r["destination_institution"]) ?? "",
            DestinationStationHost = Convert.ToString(r["destination_station_host"]) ?? "",
            DestinationPerson = Convert.ToString(r["destination_person"]) ?? "",
            CourierName = r["courier_name"] as string,
            CourierPermitNumber = r["courier_permit_number"] as string,
            MediaType = Convert.ToString(r["media_type"]) ?? "",
            MediaSerialNumber = Convert.ToString(r["media_serial"]) ?? "",
            MediaVendorId = Convert.ToString(r["media_vendor_id"]) ?? "",
            MediaProductId = Convert.ToString(r["media_product_id"]) ?? "",
            MediaInventoryCode = Convert.ToString(r["media_inventory_code"]) ?? "",
            MediaFriendlyLabel = Convert.ToString(r["media_friendly_label"]) ?? "",
            PayloadFileName = Convert.ToString(r["payload_file_name"]) ?? "",
            PayloadType = Convert.ToString(r["payload_type"]) ?? "",
            PayloadSizeGb = Convert.ToDouble(r["payload_size_gb"]),
            PayloadFilesCount = Convert.ToInt32(r["payload_files_count"]),
            PayloadSha256Hash = Convert.ToString(r["payload_sha256_hash"]) ?? "",
            ContentDescription = Convert.ToString(r["content_description"]) ?? "",
            LegalBase = Convert.ToString(r["legal_base"]) ?? "",
            OperatorUsername = Convert.ToString(r["operator_username"]) ?? "",
            Signed = Convert.ToInt32(r["signed"]) == 1,
            SignedAtUtc = r["signed_at_utc"] is string sat ? DateTime.Parse(sat) : null,
            SignedBy = r["signed_by"] as string,
            FourEyesApproverName = r["four_eyes_approver_name"] as string,
            FourEyesApproverRole = r["four_eyes_approver_role"] as string,
            Cancelled = Convert.ToInt32(r["cancelled"]) == 1,
            CancellationReason = r["cancellation_reason"] as string,
            IntegrityHash = Convert.ToString(r["integrity_hash"]) ?? ""
        };
    }

    public List<MediaAsset> GetMediaAssets(string? search = null)
    {
        var list = new List<MediaAsset>();
        var query = "SELECT * FROM media_assets WHERE 1=1";
        if (!string.IsNullOrWhiteSpace(search))
        {
            query += " AND (serial_number LIKE @s OR inventory_code LIKE @s OR friendly_name LIKE @s OR manufacturer LIKE @s OR model LIKE @s)";
        }
        query += " ORDER BY date_enrolled_utc DESC";

        using var cmd = _conn.CreateCommand();
        cmd.CommandText = query;
        if (!string.IsNullOrWhiteSpace(search)) cmd.Parameters.AddWithValue("@s", $"%{search}%");

        using var r = cmd.ExecuteReader();
        while (r.Read())
        {
            list.Add(new MediaAsset
            {
                Id = Convert.ToInt32(r["id"]),
                SerialNumber = Convert.ToString(r["serial_number"]) ?? "",
                InventoryCode = Convert.ToString(r["inventory_code"]) ?? "",
                FriendlyName = Convert.ToString(r["friendly_name"]) ?? "",
                MediaType = Convert.ToString(r["media_type"]) ?? "",
                VendorId = Convert.ToString(r["vendor_id"]) ?? "",
                ProductId = Convert.ToString(r["product_id"]) ?? "",
                Manufacturer = Convert.ToString(r["manufacturer"]) ?? "",
                Model = Convert.ToString(r["model"]) ?? "",
                CapacityBytes = Convert.ToInt64(r["capacity_bytes"]),
                MaxClassification = (ClassificationLevel)Convert.ToInt32(r["max_classification"]),
                Status = (MediaStatus)Convert.ToInt32(r["status"]),
                EncryptionStatus = Convert.ToString(r["encryption_status"]) ?? "",
                CustodianName = Convert.ToString(r["custodian_name"]) ?? "",
                CustodianUnit = Convert.ToString(r["custodian_unit"]) ?? "",
                DateEnrolledUtc = DateTime.Parse(Convert.ToString(r["date_enrolled_utc"]) ?? DateTime.UtcNow.ToString("o"))
            });
        }
        return list;
    }

    public void AddOrUpdateMedia(MediaAsset med, string opName)
    {
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = @"INSERT INTO media_assets (
            serial_number, inventory_code, friendly_name, media_type, vendor_id, product_id,
            manufacturer, model, capacity_bytes, max_classification, status, encryption_status,
            custodian_name, custodian_unit, notes, date_enrolled_utc
        ) VALUES (
            @sn, @inv, @fn, @mt, @vid, @pid,
            @man, @mod, @cap, @clf, @stat, @enc,
            @cn, @cu, @nt, @dt
        ) ON CONFLICT(serial_number) DO UPDATE SET
            inventory_code = excluded.inventory_code,
            friendly_name = excluded.friendly_name,
            max_classification = excluded.max_classification,
            status = excluded.status,
            custodian_name = excluded.custodian_name";

        cmd.Parameters.AddWithValue("@sn", med.SerialNumber);
        cmd.Parameters.AddWithValue("@inv", med.InventoryCode);
        cmd.Parameters.AddWithValue("@fn", med.FriendlyName);
        cmd.Parameters.AddWithValue("@mt", med.MediaType);
        cmd.Parameters.AddWithValue("@vid", med.VendorId);
        cmd.Parameters.AddWithValue("@pid", med.ProductId);
        cmd.Parameters.AddWithValue("@man", med.Manufacturer);
        cmd.Parameters.AddWithValue("@mod", med.Model);
        cmd.Parameters.AddWithValue("@cap", med.CapacityBytes);
        cmd.Parameters.AddWithValue("@clf", (int)med.MaxClassification);
        cmd.Parameters.AddWithValue("@stat", (int)med.Status);
        cmd.Parameters.AddWithValue("@enc", med.EncryptionStatus);
        cmd.Parameters.AddWithValue("@cn", med.CustodianName);
        cmd.Parameters.AddWithValue("@cu", med.CustodianUnit);
        cmd.Parameters.AddWithValue("@nt", (object?)med.Notes ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@dt", med.DateEnrolledUtc.ToString("o"));
        cmd.ExecuteNonQuery();

        AppendAudit("ENROLL_MEDIA", opName, $"Amprentat mediu stocare [S/N: {med.SerialNumber}, Denumire: {med.FriendlyName}, Nr: {med.InventoryCode}]", med.SerialNumber);
    }

    public void UpdateMediaPolicy(int mediaId, MediaStatus newStatus, string opName)
    {
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = "UPDATE media_assets SET status=@s WHERE id=@id";
        cmd.Parameters.AddWithValue("@s", (int)newStatus);
        cmd.Parameters.AddWithValue("@id", mediaId);
        cmd.ExecuteNonQuery();
        AppendAudit("UPDATE_POLICY", opName, $"Modificat politica acces mediu ID {mediaId} in {newStatus}");
    }

    public void UpdateMediaFriendlyName(int mediaId, string newName, string opName)
    {
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = "UPDATE media_assets SET friendly_name=@n, inventory_code=@n WHERE id=@id";
        cmd.Parameters.AddWithValue("@n", newName);
        cmd.Parameters.AddWithValue("@id", mediaId);
        cmd.ExecuteNonQuery();
        AppendAudit("RENAME_MEDIA", opName, $"Redenumit mediu ID {mediaId} in '{newName}'");
    }

    public string SanitizeMedia(int mediaId, int method, string opName, string witnessName)
    {
        var certNr = $"CERT-NIST-800-88r2-{DateTime.UtcNow.Year}-{Guid.NewGuid().ToString()[..8].ToUpperInvariant()}";
        var now = DateTime.UtcNow.ToString("o");
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = @"UPDATE media_assets SET
            status = 4,
            sanitization_method = @m,
            destruction_cert_number = @c,
            sanitized_at_utc = @d,
            sanitized_by = @op,
            verified_by = @w
            WHERE id = @id";
        cmd.Parameters.AddWithValue("@m", method);
        cmd.Parameters.AddWithValue("@c", certNr);
        cmd.Parameters.AddWithValue("@d", now);
        cmd.Parameters.AddWithValue("@op", opName);
        cmd.Parameters.AddWithValue("@w", witnessName);
        cmd.Parameters.AddWithValue("@id", mediaId);
        cmd.ExecuteNonQuery();

        AppendAudit("SANITIZE_MEDIA", opName, $"Sanitizat mediu ID {mediaId} metoda {method}, Cert: {certNr}, Martor: {witnessName}");
        return certNr;
    }

    public void AppendAudit(string action, string opName, string details, string? entityId = null)
    {
        var lastHash = "GENESIS_BLOCK";
        using var lastCmd = _conn.CreateCommand();
        lastCmd.CommandText = "SELECT entry_hash FROM audit_log ORDER BY sequence DESC LIMIT 1";
        var res = lastCmd.ExecuteScalar();
        if (res != null) lastHash = Convert.ToString(res) ?? "GENESIS_BLOCK";

        var ts = DateTime.UtcNow.ToString("o");
        var rawToHash = $"{ts}|{action}|{opName}|{details}|{entityId}|{lastHash}";
        var entryHash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(rawToHash)));

        using var insCmd = _conn.CreateCommand();
        insCmd.CommandText = @"INSERT INTO audit_log (timestamp_utc, action, operator_username, details, entity_id, previous_hash, entry_hash)
                               VALUES (@ts, @act, @op, @det, @ent, @prev, @ent_h)";
        insCmd.Parameters.AddWithValue("@ts", ts);
        insCmd.Parameters.AddWithValue("@act", action);
        insCmd.Parameters.AddWithValue("@op", opName);
        insCmd.Parameters.AddWithValue("@det", details);
        insCmd.Parameters.AddWithValue("@ent", (object?)entityId ?? DBNull.Value);
        insCmd.Parameters.AddWithValue("@prev", lastHash);
        insCmd.Parameters.AddWithValue("@ent_h", entryHash);
        insCmd.ExecuteNonQuery();

        // Anti-rollback external anchor
        try
        {
            var anchorPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "anchor.bin");
            File.WriteAllText(anchorPath, $"{entryHash}|{ts}");
        }
        catch { }
    }

    public (bool Valid, int Count, string? Error) VerifyAuditChain()
    {
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = "SELECT sequence, timestamp_utc, action, operator_username, details, entity_id, previous_hash, entry_hash FROM audit_log ORDER BY sequence ASC";
        using var r = cmd.ExecuteReader();

        var expectedPrev = "GENESIS_BLOCK";
        var count = 0;
        var lastValidHash = "";

        while (r.Read())
        {
            count++;
            var seq = r.GetInt64(0);
            var ts = r.GetString(1);
            var act = r.GetString(2);
            var op = r.GetString(3);
            var det = r.IsDBNull(4) ? "" : r.GetString(4);
            var ent = r.IsDBNull(5) ? "" : r.GetString(5);
            var prev = r.GetString(6);
            var hash = r.GetString(7);

            if (prev != expectedPrev)
            {
                return (false, count, $"Integritate compromisă la secvența #{seq}: previous_hash invalid (Așteptat: {expectedPrev}, Găsit: {prev})");
            }

            var rawToHash = $"{ts}|{act}|{op}|{det}|{(string.IsNullOrEmpty(ent) ? "" : ent)}|{prev}";
            var calcHash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(rawToHash)));

            if (calcHash != hash)
            {
                return (false, count, $"Integritate compromisă la secvența #{seq}: entry_hash calculat diferă de valoarea stocată!");
            }

            expectedPrev = hash;
            lastValidHash = hash;
        }

        // Verificare Anti-Rollback impotriva ancorei externe
        try
        {
            var anchorPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "anchor.bin");
            if (File.Exists(anchorPath) && !string.IsNullOrEmpty(lastValidHash))
            {
                var anchorContent = File.ReadAllText(anchorPath).Trim();
                var parts = anchorContent.Split('|');
                if (parts.Length > 0 && parts[0] != lastValidHash)
                {
                    return (false, count, "POSIBIL ATAC DE ROLLBACK DETECTAT: Baza de date este într-o stare anterioară ancorei externe de audit!");
                }
            }
        }
        catch { }

        return (true, count, null);
    }

    private static string ComputeTransferHash(TransferRecord tx)
    {
        var raw = $"{tx.RegistryNumber}|{tx.Classification}|{tx.TransferDateUtc:o}|{tx.SourceInstitution}|{tx.DestinationInstitution}|{tx.MediaSerialNumber}|{tx.PayloadSha256Hash}|{tx.OperatorUsername}";
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(raw)));
    }

    public void Dispose() => _conn.Dispose();
}

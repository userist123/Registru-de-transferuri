using System.Windows;
using System.Windows.Controls;
using RegistruTransferuri.Data;
using RegistruTransferuri.Hardware;
using RegistruTransferuri.Models;
using RegistruTransferuri.Security;
using RegistruTransferuri.Services;

namespace RegistruTransferuri.UI;

public partial class MainWindow : Window
{
    private readonly DatabaseContext _db;
    private readonly Operator _operator;
    private readonly SanitizationService _sanitization = new();
    private readonly PadesExportService _export = new();
    private List<DetectedMedia> _detectedMedia = new();

    public MainWindow(DatabaseContext db, Operator op)
    {
        InitializeComponent();
        _db = db;
        _operator = op;

        StatusOperator.Text = $"Operator: {op.FullName} ({op.Role}) — clearance max: {op.MaxClearance}";
        StatusAudit.Text = "Lant audit: VALID";

        ClassificationCombo.ItemsSource = Enum.GetValues<ClassificationLevel>();
        ClassificationCombo.SelectedIndex = 0;
        FilterClassCombo.ItemsSource = Enum.GetValues<ClassificationLevel>();
        FilterClassCombo.SelectedIndex = 0;

        RefreshDetectedMedia();
        LoadRegistry();
    }

    private void RefreshDetectedMedia()
    {
        try
        {
            _detectedMedia = WmiMediaDetector.DetectUsbMedia();
            DetectedMediaCombo.ItemsSource = _detectedMedia.Select(m =>
                $"{m.Model} | S/N: {m.SerialNumber} | {m.DriveLetter} | {m.CapacityBytes / 1_000_000_000} GB").ToList();
            StatusMedia.Text = $"Medii USB detectate: {_detectedMedia.Count}";
        }
        catch (Exception ex)
        {
            StatusMedia.Text = $"Eroare WMI: {ex.Message}";
        }
    }

    private void OnRefreshMedia(object s, RoutedEventArgs e) => RefreshDetectedMedia();

    private void OnRegisterTransfer(object sender, RoutedEventArgs e)
    {
        var classification = (ClassificationLevel)(ClassificationCombo.SelectedItem ?? ClassificationLevel.Neclasificat);

        if (!_operator.CanAccess(classification))
        {
            MessageBox.Show($"Clearance insuficient: sunteti autorizat pana la {_operator.MaxClearance}.",
                "Acces refuzat", MessageBoxButton.OK, MessageBoxImage.Warning);
            _db.AppendAudit("ACCESS_DENIED", _operator.Username,
                $"Incercare inregistrare {classification} peste clearance {_operator.MaxClearance}");
            return;
        }

        if (DetectedMediaCombo.SelectedIndex < 0)
        {
            MessageBox.Show("Selectati un mediu USB detectat. Introducerea manuala a seriei este interzisa.",
                "Mediu nedetectat", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var media = _detectedMedia[DetectedMediaCombo.SelectedIndex];
        var record = new TransferRecord
        {
            RegistryNumber = _db.NextRegistryNumber("MAPN", classification),
            Classification = classification,
            TransferDateUtc = DateTime.UtcNow,
            SourceInstitution = SourceInstBox.Text.Trim(),
            DestinationInstitution = DestInstBox.Text.Trim(),
            SourcePerson = SourcePersonBox.Text.Trim(),
            DestinationPerson = DestPersonBox.Text.Trim(),
            MediaType = "USB",
            MediaSerialNumber = media.SerialNumber,
            ContentDescription = ContentBox.Text.Trim(),
            OperatorUsername = _operator.Username
        };

        _db.InsertTransfer(record);
        MessageBox.Show($"Transfer inregistrat: {record.RegistryNumber}\nHash integritate: {record.IntegrityHash[..16]}...",
            "Succes", MessageBoxButton.OK, MessageBoxImage.Information);
        LoadRegistry();
    }

    private void LoadRegistry()
    {
        var records = new List<TransferRecord>();
        using var cmd = _db.RawConnection.CreateCommand();
        cmd.CommandText = @"SELECT registry_number, classification, transfer_date_utc, source_institution,
            destination_institution, source_person, destination_person, media_type, media_serial,
            media_inventory_code, content_description, operator_username, signed, signed_at_utc,
            signed_by, cancelled, cancellation_reason, integrity_hash
            FROM transfers ORDER BY transfer_date_utc DESC LIMIT 500";
        using var r = cmd.ExecuteReader();
        while (r.Read())
        {
            records.Add(new TransferRecord
            {
                RegistryNumber = r.GetString(0),
                Classification = (ClassificationLevel)r.GetInt32(1),
                TransferDateUtc = DateTime.Parse(r.GetString(2)),
                SourceInstitution = r.GetString(3),
                DestinationInstitution = r.GetString(4),
                SourcePerson = r.GetString(5),
                DestinationPerson = r.GetString(6),
                MediaType = r.GetString(7),
                MediaSerialNumber = r.GetString(8),
                MediaInventoryCode = r.GetString(9),
                ContentDescription = r.GetString(10),
                OperatorUsername = r.GetString(11),
                Signed = r.GetInt32(12) == 1,
                SignedAtUtc = r.IsDBNull(13) ? null : DateTime.Parse(r.GetString(13)),
                SignedBy = r.IsDBNull(14) ? null : r.GetString(14),
                Cancelled = r.GetInt32(15) == 1,
                CancellationReason = r.IsDBNull(16) ? null : r.GetString(16),
                IntegrityHash = r.GetString(17)
            });
        }

        RegistryGrid.ItemsSource = records
            .Where(t => _operator.CanAccess(t.Classification))
            .ToList();
    }

    private void OnSearchChanged(object s, RoutedEventArgs e)
    {
        if (RegistryGrid.ItemsSource is not List<TransferRecord> all) return;
        var q = SearchBox?.Text?.Trim() ?? "";
        var filter = FilterClassCombo?.SelectedItem as ClassificationLevel?;
        RegistryGrid.ItemsSource = all.Where(t =>
            (string.IsNullOrEmpty(q) ||
             t.RegistryNumber.Contains(q, StringComparison.OrdinalIgnoreCase) ||
             t.SourceInstitution.Contains(q, StringComparison.OrdinalIgnoreCase) ||
             t.DestinationInstitution.Contains(q, StringComparison.OrdinalIgnoreCase) ||
             t.SourcePerson.Contains(q, StringComparison.OrdinalIgnoreCase) ||
             t.MediaSerialNumber.Contains(q, StringComparison.OrdinalIgnoreCase)) &&
            (filter is null || t.Classification == filter)).ToList();
    }

    private void OnTransferSelected(object s, SelectionChangedEventArgs e) { }

    private void OnSignTransfer(object s, RoutedEventArgs e)
    {
        if (RegistryGrid.SelectedItem is not TransferRecord t) return;
        using var cmd = _db.RawConnection.CreateCommand();
        cmd.CommandText = @"UPDATE transfers SET signed=1, signed_at_utc=$t, signed_by=$o
                            WHERE registry_number=$rn AND signed=0";
        cmd.Parameters.AddWithValue("$t", DateTime.UtcNow.ToString("O"));
        cmd.Parameters.AddWithValue("$o", _operator.Username);
        cmd.Parameters.AddWithValue("$rn", t.RegistryNumber);
        cmd.ExecuteNonQuery();
        _db.AppendAudit("SIGN_TRANSFER", _operator.Username, $"nr={t.RegistryNumber}");
        LoadRegistry();
    }

    private void OnCancelTransfer(object s, RoutedEventArgs e)
    {
        if (RegistryGrid.SelectedItem is not TransferRecord t) return;
        var reason = Microsoft.VisualBasic.Interaction.InputBox(
            "Justificare anulare (obligatorie):", "Anulare inregistrare", "");
        if (string.IsNullOrWhiteSpace(reason)) return;
        using var cmd = _db.RawConnection.CreateCommand();
        cmd.CommandText = @"UPDATE transfers SET cancelled=1, cancellation_reason=$r
                            WHERE registry_number=$rn";
        cmd.Parameters.AddWithValue("$r", reason);
        cmd.Parameters.AddWithValue("$rn", t.RegistryNumber);
        cmd.ExecuteNonQuery();
        _db.AppendAudit("CANCEL_TRANSFER", _operator.Username, $"nr={t.RegistryNumber}; motiv={reason}");
        LoadRegistry();
    }

    private void OnExportPdf(object s, RoutedEventArgs e)
    {
        var records = (RegistryGrid.ItemsSource as List<TransferRecord>) ?? new();
        var pdf = _export.GenerateRegistryReportPdf(records, "MAPN", "(radacina Merkle)", DateTime.UtcNow);
        var path = System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Desktop),
            $"registru-{DateTime.UtcNow:yyyyMMdd-HHmmss}.pdf");
        System.IO.File.WriteAllBytes(path, pdf);
        _db.AppendAudit("EXPORT_PDF", _operator.Username, $"fisier={path}; inregistrari={records.Count}");
        MessageBox.Show($"Raport exportat: {path}", "Export", MessageBoxButton.OK, MessageBoxImage.Information);
    }

    private void OnExportCsv(object s, RoutedEventArgs e)
    {
        var records = (RegistryGrid.ItemsSource as List<TransferRecord>) ?? new();
        var path = System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Desktop),
            $"registru-{DateTime.UtcNow:yyyyMMdd-HHmmss}.csv");
        using var w = new System.IO.StreamWriter(path, false, System.Text.Encoding.UTF8);
        w.WriteLine("NrRegistru;Clasificare;DataUTC;Sursa;Destinatie;Predator;Primitor;TipMediu;Serie;Hash");
        foreach (var r in records)
            w.WriteLine($"{r.RegistryNumber};{r.Classification};{r.TransferDateUtc:O};{r.SourceInstitution};" +
                $"{r.DestinationInstitution};{r.SourcePerson};{r.DestinationPerson};{r.MediaType};" +
                $"{r.MediaSerialNumber};{r.IntegrityHash}");
        _db.AppendAudit("EXPORT_CSV", _operator.Username, $"fisier={path}; inregistrari={records.Count}");
    }

    private void OnVerifyChain(object s, RoutedEventArgs e)
    {
        var compromised = _db.VerifyAuditChain();
        AuditResult.Text = compromised < 0
            ? "Lant audit: VALID — nicio alterare detectata."
            : $"COMPROMIS la secventa {compromised}!";
        StatusAudit.Text = compromised < 0 ? "Lant audit: VALID" : $"COMPROMIS @ {compromised}";
    }

    private void OnMerkleRoot(object s, RoutedEventArgs e)
    {
        var hashes = new List<string>();
        using var cmd = _db.RawConnection.CreateCommand();
        cmd.CommandText = "SELECT entry_hash FROM audit_log WHERE date(timestamp_utc)=date('now') ORDER BY sequence";
        using var r = cmd.ExecuteReader();
        while (r.Read()) hashes.Add(r.GetString(0));
        var root = MerkleTree.ComputeRoot(hashes);
        AuditResult.Text = $"Radacina Merkle ({hashes.Count} intrari): {root[..32]}...";
        _db.AppendAudit("MERKLE_ROOT", _operator.Username, $"root={root}; count={hashes.Count}");
    }
}

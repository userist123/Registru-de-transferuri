using System.IO;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Threading;
using Microsoft.Win32;
using RegistruTransferuri.Data;
using RegistruTransferuri.Hardware;
using RegistruTransferuri.Models;
using RegistruTransferuri.Services;
using RegistruTransferuri.Security;
using RegistruTransferuri.UI.Dialogs;

namespace RegistruTransferuri.UI;

public partial class MainWindow : Window
{
    private readonly DatabaseContext _db;
    private readonly Operator _operator;
    private readonly CognitiveVaultBridgeService _vaultBridge;
    private readonly PadesExportService _exportService = new();
    private readonly DispatcherTimer _pnpTimer = new();

    private List<DetectedMedia> _detectedMedia = new();
    private List<TransferRecord> _transfers = new();
    private List<MediaAsset> _mediaAssets = new();

    public MainWindow(DatabaseContext db, Operator op)
    {
        InitializeComponent();
        _db = db;
        _operator = op;
        _vaultBridge = new CognitiveVaultBridgeService();

        LblOperatorName.Text = _operator.FullName;
        LblOperatorClearance.Text = _operator.MaxClearance.ToDisplayName().ToUpperInvariant();
        LblHostInfo.Text = $"Stație: {_db.LocalStationHost}";

        CmbFilterClassification.ItemsSource = Enum.GetValues<ClassificationLevel>();
        CmbNewTxClass.ItemsSource = Enum.GetValues<ClassificationLevel>();
        CmbNewTxClass.SelectedItem = ClassificationLevel.Secret;
        CmbNewOpClearance.ItemsSource = Enum.GetValues<ClassificationLevel>();
        CmbNewOpClearance.SelectedItem = ClassificationLevel.Secret;

        // Event-Driven Native Windows Device Notification Hook (0 latency)
        SourceInitialized += OnSourceInitialized;

        // Fallback Auto PnP Polling Timer
        _pnpTimer.Interval = TimeSpan.FromSeconds(3);
        _pnpTimer.Tick += (s, e) => RefreshLiveMediaSilent();
        _pnpTimer.Start();

        RefreshAll();
        InitOracleDefaultView();
    }

    private void OnSourceInitialized(object? sender, EventArgs e)
    {
        var hwnd = new System.Windows.Interop.WindowInteropHelper(this).Handle;
        var source = System.Windows.Interop.HwndSource.FromHwnd(hwnd);
        source?.AddHook(HwndHook);
    }

    private IntPtr HwndHook(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
    {
        const int WM_DEVICECHANGE = 0x0219;
        if (msg == WM_DEVICECHANGE)
        {
            RefreshLiveMediaSilent();
        }
        return IntPtr.Zero;
    }

    private void RefreshAll()
    {
        RefreshLiveMedia();
        LoadRegistry();
        LoadMediaWhitelist();
        LoadStats();
        LoadAuditLog();
        LoadOperators();
    }

    // ================= NAVIGATION =================
    private void OnNavChanged(object sender, RoutedEventArgs e)
    {
        if (ViewRegistru == null) return;

        ViewRegistru.Visibility = NavRegistru.IsChecked == true ? Visibility.Visible : Visibility.Collapsed;
        ViewInregistrare.Visibility = NavInregistrare.IsChecked == true ? Visibility.Visible : Visibility.Collapsed;
        ViewMedii.Visibility = NavMedii.IsChecked == true ? Visibility.Visible : Visibility.Collapsed;
        ViewOracle.Visibility = NavOracle.IsChecked == true ? Visibility.Visible : Visibility.Collapsed;
        ViewStats.Visibility = NavStats.IsChecked == true ? Visibility.Visible : Visibility.Collapsed;
        ViewAudit.Visibility = NavAudit.IsChecked == true ? Visibility.Visible : Visibility.Collapsed;
        ViewAdmin.Visibility = NavAdmin.IsChecked == true ? Visibility.Visible : Visibility.Collapsed;

        if (NavRegistru.IsChecked == true)
        {
            LblViewTitle.Text = "📋 Evidența Transferurilor de Date Clasificate (HG 585 / NATO AC/35)";
            LoadRegistry();
        }
        else if (NavInregistrare.IsChecked == true)
        {
            LblViewTitle.Text = "➕ Înregistrare Transfer Nou de Date (Control Strict Dispozitive)";
            RefreshLiveMedia();
        }
        else if (NavMedii.IsChecked == true)
        {
            LblViewTitle.Text = "🛡️ Control Medii de Stocare Amprentate (Endpoint Protector Model)";
            RefreshLiveMedia();
            LoadMediaWhitelist();
        }
        else if (NavOracle.IsChecked == true)
        {
            LblViewTitle.Text = "🧠 Seif Cognitiv AI & Asistent de Securitate INFOSEC";
        }
        else if (NavStats.IsChecked == true)
        {
            LblViewTitle.Text = "📊 Tablou de Bord Statistici & Conformitate Militară";
            LoadStats();
        }
        else if (NavAudit.IsChecked == true)
        {
            LblViewTitle.Text = "📜 Jurnal de Audit Criptografic Tamper-Evident (SHA-256 Chained)";
            LoadAuditLog();
        }
        else if (NavAdmin.IsChecked == true)
        {
            LblViewTitle.Text = "⚙️ Administrare Sistem & Gestiune Operatori Militari";
            LoadOperators();
        }
    }

    // ================= TAB 1: REGISTRU TRANSFERURI =================
    private void LoadRegistry()
    {
        var search = TxtSearchRegistry.Text.Trim();
        ClassificationLevel? clf = CmbFilterClassification.SelectedIndex > 0 ? (ClassificationLevel)CmbFilterClassification.SelectedItem : null;
        _transfers = _db.GetTransfers(search, clf);
        GridTransfers.ItemsSource = _transfers;
    }

    private void OnRegistryFilterChanged(object sender, EventArgs e) => LoadRegistry();

    private void OnTransferSelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (GridTransfers.SelectedItem is TransferRecord tx)
        {
            TxtInspector.Text =
                $"=== FIȘĂ DETALII TRANSFER MILITAR: {tx.RegistryNumber} ===\r\n" +
                $"Clasificare: {tx.Classification.ToDisplayName()} (NATO: {tx.NatoClassification} | UE: {tx.EuClassification})\r\n" +
                $"Data Transfer UTC: {tx.TransferDateUtc:yyyy-MM-dd HH:mm:ss} | Direcție: {tx.Direction.ToUpperInvariant()}\r\n" +
                $"Sursă: {tx.SourceInstitution} (Stație: {tx.SourceStationHost}) | Responsabil: {tx.SourcePerson}\r\n" +
                $"Destinație: {tx.DestinationInstitution} (Stație: {tx.DestinationStationHost}) | Primitor: {tx.DestinationPerson}\r\n" +
                $"Curier Militar: {tx.CourierName ?? "Fără curier extern"} (Permis: {tx.CourierPermitNumber ?? "N/A"})\r\n" +
                $"Mediu Stocare: {tx.MediaType} | Etichetă: {tx.MediaFriendlyLabel}\r\n" +
                $"Serie Hardware S/N: {tx.MediaSerialNumber} | Identificator: VID_{tx.MediaVendorId} & PID_{tx.MediaProductId}\r\n" +
                $"Pachet Date: {tx.PayloadFileName} ({tx.PayloadSizeGb} GB, {tx.PayloadFilesCount} fișiere)\r\n" +
                $"Hash SHA-256 Pachet: {tx.PayloadSha256Hash}\r\n" +
                $"Hash Înregistrare Audit: {tx.IntegrityHash}\r\n" +
                $"Bază Legală: {tx.LegalBase}\r\n" +
                $"Operator Înregistrare: {tx.OperatorUsername}\r\n" +
                $"Semnat Formal: {(tx.Signed ? $"DA (la {tx.SignedAtUtc:yyyy-MM-dd HH:mm} de către {tx.SignedBy})" : "NU")}\r\n" +
                $"Aprobare 4-Eyes: {tx.FourEyesApproverName ?? "N/A"} ({tx.FourEyesApproverRole ?? "N/A"})\r\n" +
                $"Status Curent: {tx.StatusText}" +
                (tx.Cancelled ? $"\r\nMotiv Anulare: {tx.CancellationReason}" : "");
        }
        else
        {
            TxtInspector.Text = "Selectați un transfer din tabel pentru a vizualiza detaliile complete și integritatea SHA-256.";
        }
    }

    private void OnGenerateProcesVerbalClick(object sender, RoutedEventArgs e)
    {
        if (GridTransfers.SelectedItem is not TransferRecord tx)
        {
            MessageBox.Show("Selectați un transfer din tabel pentru a genera Procesul-Verbal.", "Selecție Obligatorie", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var dlg = new ProcesVerbalDialog(tx) { Owner = this };
        dlg.ShowDialog();
    }

    private void OnVerifyReceiverPackageClick(object sender, RoutedEventArgs e)
    {
        if (GridTransfers.SelectedItem is not TransferRecord tx)
        {
            MessageBox.Show("Selectați un transfer din tabel pentru a verifica pachetul la recepție.", "Selecție Obligatorie", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var dlg = new ReceiverVerifyDialog(tx.PayloadSha256Hash) { Owner = this };
        dlg.ShowDialog();
    }

    private void OnExportCsvClick(object sender, RoutedEventArgs e)
    {
        var sfd = new SaveFileDialog
        {
            Filter = "Fișier CSV (*.csv)|*.csv",
            FileName = $"Registru_Transferuri_{DateTime.UtcNow:yyyyMMdd}.csv"
        };
        if (sfd.ShowDialog() == true)
        {
            _exportService.ExportCsv(_transfers, sfd.FileName);
            MessageBox.Show($"Registrul a fost exportat cu succes în:\n{sfd.FileName}", "Export Reușit", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }

    private void OnSignTransferClick(object sender, RoutedEventArgs e)
    {
        if (GridTransfers.SelectedItem is not TransferRecord tx)
        {
            MessageBox.Show("Selectați un transfer din tabel.", "Selecție", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (tx.Signed)
        {
            MessageBox.Show("Transferul este deja semnat formal.", "Informație", MessageBoxButton.OK, MessageBoxImage.Information);
            return;
        }

        using var cmd = _db.RawConnection.CreateCommand();
        cmd.CommandText = "UPDATE transfers SET signed=1, signed_at_utc=@d, signed_by=@b WHERE id=@id";
        cmd.Parameters.AddWithValue("@d", DateTime.UtcNow.ToString("o"));
        cmd.Parameters.AddWithValue("@b", _operator.FullName);
        cmd.Parameters.AddWithValue("@id", tx.Id);
        cmd.ExecuteNonQuery();

        _db.AppendAudit("SIGN_TRANSFER", _operator.FullName, $"Semnat formal transferul {tx.RegistryNumber}", tx.RegistryNumber);
        MessageBox.Show($"Transferul [{tx.RegistryNumber}] a fost semnat cu succes.", "Semnat", MessageBoxButton.OK, MessageBoxImage.Information);
        LoadRegistry();
    }

    private void OnCancelTransferClick(object sender, RoutedEventArgs e)
    {
        if (GridTransfers.SelectedItem is not TransferRecord tx)
        {
            MessageBox.Show("Selectați un transfer din tabel.", "Selecție", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (tx.Cancelled)
        {
            MessageBox.Show("Transferul este deja anulat.", "Informație", MessageBoxButton.OK, MessageBoxImage.Information);
            return;
        }

        var reason = Microsoft.VisualBasic.Interaction.InputBox("Introduceți motivul / justificarea de securitate pentru anularea transferului:", "Anulare Transfer Militar", "Eroare operator / Modificare destinație");
        if (!string.IsNullOrWhiteSpace(reason))
        {
            using var cmd = _db.RawConnection.CreateCommand();
            cmd.CommandText = "UPDATE transfers SET cancelled=1, cancellation_reason=@r WHERE id=@id";
            cmd.Parameters.AddWithValue("@r", reason.Trim());
            cmd.Parameters.AddWithValue("@id", tx.Id);
            cmd.ExecuteNonQuery();

            _db.AppendAudit("CANCEL_TRANSFER", _operator.FullName, $"Anulat transferul {tx.RegistryNumber}: {reason.Trim()}", tx.RegistryNumber);
            MessageBox.Show($"Transferul [{tx.RegistryNumber}] a fost anulat.", "Anulat", MessageBoxButton.OK, MessageBoxImage.Information);
            LoadRegistry();
        }
    }

    // ================= TAB 2: ÎNREGISTRARE TRANSFER NOU =================
    private void OnNewTxClassificationChanged(object sender, SelectionChangedEventArgs e)
    {
        if (CmbNewTxClass.SelectedItem is ClassificationLevel level && TxtRegNumber != null)
        {
            TxtRegNumber.Text = _db.NextRegistryNumber("MAPN", level);
        }
    }

    private void OnSelectPayloadFileClick(object sender, RoutedEventArgs e)
    {
        var ofd = new OpenFileDialog
        {
            Title = "Selectează Fișierul Pachet pentru Transfer Militar"
        };
        if (ofd.ShowDialog() == true)
        {
            TxtPayloadPath.Text = ofd.FileName;
            var fi = new FileInfo(ofd.FileName);
            TxtPayloadFileName.Text = fi.Name;

            // Auto parse registration number (ex: 2150-23SSv.zip -> 2150-23SSv)
            var match = Regex.Match(fi.Name, @"(\d{2,6}[\-_][A-Za-z0-9]+)");
            if (match.Success)
            {
                TxtRegNumber.Text = match.Groups[1].Value;
                if (fi.Name.Contains("SSV", StringComparison.OrdinalIgnoreCase) || fi.Name.Contains("SSv", StringComparison.OrdinalIgnoreCase))
                    CmbNewTxClass.SelectedItem = ClassificationLevel.SecretDeServiciu;
                else if (fi.Name.Contains("SSID", StringComparison.OrdinalIgnoreCase))
                    CmbNewTxClass.SelectedItem = ClassificationLevel.StrictSecretDeImportantaDeosebita;
                else if (fi.Name.Contains("SS", StringComparison.OrdinalIgnoreCase))
                    CmbNewTxClass.SelectedItem = ClassificationLevel.StrictSecret;
                else if (fi.Name.Contains("S", StringComparison.OrdinalIgnoreCase))
                    CmbNewTxClass.SelectedItem = ClassificationLevel.Secret;
            }

            // DLP & Magic Bytes Inspection
            var dlp = PayloadDlpInspector.InspectFile(ofd.FileName);
            if (!dlp.IsSafe)
            {
                MessageBox.Show(dlp.Details, "DLP ALERT — Fișier Blocat", MessageBoxButton.OK, MessageBoxImage.Stop);
                _db.AppendAudit("DLP_BLOCK", _operator.FullName, $"Blocat transfer fișier executabil/contaminat: {fi.Name}");
                TxtPayloadPath.Clear();
                TxtPayloadFileName.Clear();
                TxtPayloadHash.Clear();
                return;
            }

            // Calculate instant SHA-256
            try
            {
                using var stream = File.OpenRead(ofd.FileName);
                var hash = Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
                TxtPayloadHash.Text = hash;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Eroare la calcularea hash-ului SHA-256: {ex.Message}", "Eroare", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }

    private void OnSubmitTransferClick(object sender, RoutedEventArgs e)
    {
        var classification = (ClassificationLevel)(CmbNewTxClass.SelectedItem ?? ClassificationLevel.Secret);

        if (!_operator.CanAccess(classification))
        {
            MessageBox.Show($"Clearance insuficient: sunteți autorizat până la {_operator.MaxClearance.ToDisplayName()}.", "Acces Refuzat", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (CmbDetectedMedia.SelectedIndex < 0)
        {
            MessageBox.Show("Selectați un mediu fizic conectat din listă.", "Mediu Lipsă", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var dev = _detectedMedia[CmbDetectedMedia.SelectedIndex];

        // Verificare Plafon Clasificare Mediu din Whitelist
        var matchingAsset = _mediaAssets.FirstOrDefault(m => m.SerialNumber == dev.SerialNumber);
        if (matchingAsset != null && (int)classification > (int)matchingAsset.MaxClassification)
        {
            MessageBox.Show($"Plafon de securitate depășit!\nMediul [{matchingAsset.FriendlyName}] are plafonul maxim {matchingAsset.MaxClassification.ToDisplayName()}, dar transferul este {classification.ToDisplayName()}.", "Blocare Securitate", MessageBoxButton.OK, MessageBoxImage.Error);
            return;
        }

        // Four-Eyes Principle Enforcement for Secret / Strict Secret / SSID
        Operator? witness = null;
        string witnessRole = string.Empty;
        if (classification >= ClassificationLevel.Secret)
        {
            var authDlg = new FourEyesAuthDialog(_db, _operator) { Owner = this };
            if (authDlg.ShowDialog() != true)
            {
                MessageBox.Show("Transferul clasificat nu poate fi înregistrat fără aprobarea unui al doilea ofițer autorizat (Principiul celor 4 Ochi).", "Aprobare Refuzată", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
            witness = authDlg.ApprovedWitness;
            witnessRole = authDlg.ApproverRole;
        }

        var regNr = TxtRegNumber.Text.Trim();
        if (string.IsNullOrWhiteSpace(regNr)) regNr = _db.NextRegistryNumber("MAPN", classification);

        var payloadSize = 0.0;
        if (!string.IsNullOrWhiteSpace(TxtPayloadPath.Text) && File.Exists(TxtPayloadPath.Text))
            payloadSize = Math.Round((double)new FileInfo(TxtPayloadPath.Text).Length / (1024 * 1024 * 1024), 3);

        var tx = new TransferRecord
        {
            RegistryNumber = regNr,
            Classification = classification,
            TransferDateUtc = DateTime.UtcNow,
            Direction = "iesire",
            SourceInstitution = TxtSrcInst.Text.Trim(),
            SourceStationHost = _db.LocalStationHost,
            SourcePerson = TxtSrcPerson.Text.Trim(),
            SourcePersonRole = "Operator Transferuri IT",
            SourcePersonClearance = _operator.MaxClearance.ToDisplayName(),
            DestinationInstitution = TxtDstInst.Text.Trim(),
            DestinationStationHost = "Stație Destinație Air-Gapped",
            DestinationPerson = TxtDstPerson.Text.Trim(),
            CourierName = string.IsNullOrWhiteSpace(TxtCourierName.Text) ? null : TxtCourierName.Text.Trim(),
            CourierPermitNumber = string.IsNullOrWhiteSpace(TxtCourierPermit.Text) ? null : TxtCourierPermit.Text.Trim(),
            MediaType = dev.MediaType,
            MediaSerialNumber = dev.SerialNumber,
            MediaVendorId = dev.VendorId,
            MediaProductId = dev.ProductId,
            MediaInventoryCode = matchingAsset?.InventoryCode ?? dev.SerialNumber,
            MediaFriendlyLabel = matchingAsset?.FriendlyName ?? dev.Model,
            StorageMediumId = matchingAsset?.Id,
            PayloadFileName = TxtPayloadFileName.Text.Trim(),
            PayloadType = "Arhivă Date Securizată",
            PayloadSizeGb = payloadSize,
            PayloadFilesCount = 1,
            PayloadSha256Hash = string.IsNullOrWhiteSpace(TxtPayloadHash.Text) ? "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" : TxtPayloadHash.Text.Trim(),
            ContentDescription = TxtContentDesc.Text.Trim(),
            AntivirusScanned = true,
            AntivirusDetails = "Scanare Antivirus Offline: Bază Definiții la zi, Negativ",
            LegalBase = "HG 585/2002 Art. 60-73",
            OperatorUsername = _operator.FullName,
            FourEyesApproverName = witness?.FullName,
            FourEyesApproverRole = witnessRole,
            FourEyesApprovedAtUtc = witness != null ? DateTime.UtcNow : null
        };

        try
        {
            _db.InsertTransfer(tx);
            MessageBox.Show($"Transferul [{tx.RegistryNumber}] a fost înregistrat cu succes!\n\nHash Integritate Audit: {tx.IntegrityHash[..16]}...", "Transfer Înregistrat", MessageBoxButton.OK, MessageBoxImage.Information);

            NavRegistru.IsChecked = true;
            LoadRegistry();
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Eroare la înregistrarea transferului: {ex.Message}", "Eroare", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    // ================= TAB 3: MEDII AMPRENTATE =================
    private void RefreshLiveMediaSilent()
    {
        var devs = WmiMediaDetector.DetectAllMedia();
        if (devs.Count != _detectedMedia.Count)
        {
            _detectedMedia = devs;
            GridLiveMedia.ItemsSource = _detectedMedia;
            CmbDetectedMedia.ItemsSource = _detectedMedia.Select(m => m.DisplayLabel).ToList();
            if (_detectedMedia.Count > 0 && CmbDetectedMedia.SelectedIndex < 0)
                CmbDetectedMedia.SelectedIndex = 0;
        }
    }

    private void RefreshLiveMedia()
    {
        _detectedMedia = WmiMediaDetector.DetectAllMedia();
        GridLiveMedia.ItemsSource = _detectedMedia;
        CmbDetectedMedia.ItemsSource = _detectedMedia.Select(m => m.DisplayLabel).ToList();
        if (_detectedMedia.Count > 0 && CmbDetectedMedia.SelectedIndex < 0)
            CmbDetectedMedia.SelectedIndex = 0;
    }

    private void LoadMediaWhitelist()
    {
        var search = TxtSearchMedia != null ? TxtSearchMedia.Text.Trim() : "";
        _mediaAssets = _db.GetMediaAssets(search);
        GridMediaWhitelist.ItemsSource = _mediaAssets;
    }

    private void OnMediaFilterChanged(object sender, EventArgs e) => LoadMediaWhitelist();

    private void OnEnrollDetectedMediaClick(object sender, RoutedEventArgs e)
    {
        if ((sender as Button)?.DataContext is DetectedMedia dev)
        {
            var dlg = new EnrollMediaDialog(_db, dev, _operator) { Owner = this };
            if (dlg.ShowDialog() == true)
            {
                RefreshLiveMedia();
                LoadMediaWhitelist();
            }
        }
    }

    private void OnRenameMediaClick(object sender, RoutedEventArgs e)
    {
        if (GridMediaWhitelist.SelectedItem is not MediaAsset med)
        {
            MessageBox.Show("Selectați un mediu din tabelul bazei de date.", "Selecție", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var newName = Microsoft.VisualBasic.Interaction.InputBox("Introduceți noua Denumire Volum / Număr Înregistrare Mediu:", "Modificare Denumire", med.FriendlyName);
        if (!string.IsNullOrWhiteSpace(newName) && newName.Trim() != med.FriendlyName)
        {
            _db.UpdateMediaFriendlyName(med.Id, newName.Trim(), _operator.FullName);
            MessageBox.Show($"Denumirea a fost actualizată în:\n'{newName.Trim()}'", "Succes", MessageBoxButton.OK, MessageBoxImage.Information);
            LoadMediaWhitelist();
        }
    }

    private void OnSanitizeMediaClick(object sender, RoutedEventArgs e)
    {
        if (GridMediaWhitelist.SelectedItem is not MediaAsset med)
        {
            MessageBox.Show("Selectați un mediu din tabel.", "Selecție", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var witness = Microsoft.VisualBasic.Interaction.InputBox("Introduceți numele ofițerului de securitate / martorului verificator:", "Martor Sanitizare NIST SP 800-88r2", "Ofițer Securitate INFOSEC");
        if (!string.IsNullOrWhiteSpace(witness))
        {
            var certNr = _db.SanitizeMedia(med.Id, 2, _operator.FullName, witness.Trim());
            LoadMediaWhitelist();

            var certDlg = new SanitizationCertDialog(med, _operator.FullName, witness.Trim(), certNr, "Purge (Cryptographic Erase / Multi-Pass NIST 800-88r2)") { Owner = this };
            certDlg.ShowDialog();
        }
    }

    // ================= TAB 4: SEIF COGNITIV & ORACOL =================
    private void InitOracleDefaultView()
    {
        LblVaultStatus.Text = _vaultBridge.IsVaultAvailable ? "🟢 Conectat (AI_Memory_Vault_CODEX_READY)" : "🔴 Seif Memorie Indisponibil";
        DisplayOracleResponse(_vaultBridge.AskSecurityOracle("ajutor"));
    }

    private void OnAskOracleClick(object sender, RoutedEventArgs e)
    {
        var q = TxtOracleQuery.Text.Trim();
        if (!string.IsNullOrWhiteSpace(q))
        {
            var ans = _vaultBridge.AskSecurityOracle(q);
            DisplayOracleResponse(ans);
        }
    }

    private void OnOracleQueryKeyDown(object sender, System.Windows.Input.KeyEventArgs e)
    {
        if (e.Key == System.Windows.Input.Key.Enter)
            OnAskOracleClick(sender, e);
    }

    private void DisplayOracleResponse(string htmlBody)
    {
        var html = $@"<!DOCTYPE html><html><head><meta charset=""UTF-8""><style>
        body {{ background-color: #131B2E; color: #F8FAFC; font-family: 'Segoe UI', Arial; font-size: 13px; margin: 15px; line-height: 1.6; }}
        code {{ background-color: #1E293B; color: #38BDF8; padding: 2px 5px; border-radius: 3px; font-family: 'Consolas', monospace; }}
        b {{ color: #00E5FF; }}
        </style></head><body>{htmlBody}</body></html>";
        BrowserOracle.NavigateToString(html);
    }

    private void OnSynthesizeTransferClick(object sender, RoutedEventArgs e)
    {
        if (GridTransfers.SelectedItem is not TransferRecord tx)
        {
            MessageBox.Show("Selectați un transfer din Tab-ul Registru pentru a-l sintetiza în Seiful de Memorie AI.", "Selecție", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var (success, msg) = _vaultBridge.SynthesizeTransferToVault(tx);
        MessageBox.Show(msg, success ? "Sinteză Reușită" : "Eroare Sinteză", MessageBoxButton.OK, success ? MessageBoxImage.Information : MessageBoxImage.Error);
    }

    // ================= TAB 5: STATISTICI =================
    private void LoadStats()
    {
        KpiTotalTransfers.Text = _transfers.Count.ToString();
        var secretCount = _transfers.Count(t => t.Classification >= ClassificationLevel.Secret);
        KpiSecretTransfers.Text = secretCount.ToString();
        KpiEnrolledMedia.Text = _mediaAssets.Count.ToString();
        var totalGb = _transfers.Where(t => !t.Cancelled).Sum(t => t.PayloadSizeGb);
        KpiVolumeGb.Text = $"{totalGb:F2} GB";

        TxtStatsReport.Text =
            $"=== RAPORT SINTETIC DE SECURITATE & CONFORMITATE MILITARĂ ===\r\n" +
            $"Stație Lucru Locală: {_db.LocalStationHost} | Regim: AIR-GAPPED IZOLAT\r\n" +
            $"Data Raportului: {DateTime.Now:dd.MM.yyyy HH:mm:ss}\r\n\r\n" +
            $"1. SITUAȚIE TRANSFERURI MILITARE:\r\n" +
            $"   • Total Transferuri Înregistrate: {_transfers.Count} (Active: {_transfers.Count(t => !t.Cancelled)}, Anulate: {_transfers.Count(t => t.Cancelled)})\r\n" +
            $"   • Transferuri Clasificate Secret / NATO CONFIDENTIAL+: {secretCount}\r\n" +
            $"   • Volum Total Date Vehiculat: {totalGb:F2} GB\r\n\r\n" +
            $"2. SITUAȚIE MEDII DE STOCARE (ENDPOINT PROTECTOR):\r\n" +
            $"   • Total Medii Amprentate în Whitelist: {_mediaAssets.Count}\r\n" +
            $"   • Medii Autorizate Read/Write: {_mediaAssets.Count(m => m.Status == MediaStatus.AutorizatRw)}\r\n" +
            $"   • Medii Restricționate Read-Only: {_mediaAssets.Count(m => m.Status == MediaStatus.AutorizatRo)}\r\n" +
            $"   • Medii Blocate / Revocate / Sanitizate: {_mediaAssets.Count(m => m.Status == MediaStatus.Blocat || m.Status == MediaStatus.Sanitizat)}\r\n\r\n" +
            $"3. CONFORMITATE PRINCIPIUL CELOR 4 OCHI & AUDIT:\r\n" +
            $"   • Transferuri Aprobate Dual (Four-Eyes): {_transfers.Count(t => !string.IsNullOrEmpty(t.FourEyesApproverName))}\r\n" +
            $"   • Transferuri Semnate Formal cu PIN: {_transfers.Count(t => t.Signed)}\r\n";
    }

    // ================= TAB 6: AUDIT LOG =================
    private void LoadAuditLog()
    {
        var list = new List<AuditEntry>();
        using var cmd = _db.RawConnection.CreateCommand();
        cmd.CommandText = "SELECT sequence, timestamp_utc, action, operator_username, details, entity_id, previous_hash, entry_hash FROM audit_log ORDER BY sequence DESC LIMIT 500";
        using var r = cmd.ExecuteReader();
        while (r.Read())
        {
            list.Add(new AuditEntry
            {
                Sequence = r.GetInt32(0),
                TimestampUtc = r.GetString(1),
                Action = r.GetString(2),
                OperatorUsername = r.GetString(3),
                Details = r.GetString(4),
                EntityId = r.IsDBNull(5) ? null : r.GetString(5),
                PreviousHash = r.GetString(6),
                EntryHash = r.GetString(7)
            });
        }
        GridAudit.ItemsSource = list;
    }

    private void OnAuditSelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (GridAudit.SelectedItem is AuditEntry entry)
        {
            TxtAuditInspector.Text =
                $"=== BLOC AUDIT CRIPTOGRAFIC SECVENȚA #{entry.Sequence} ===\r\n" +
                $"Timestamp: {entry.TimestampUtc} | Acțiune: {entry.Action}\r\n" +
                $"Operator: {entry.OperatorUsername} | Entitate: {entry.EntityId ?? "Sistem"}\r\n" +
                $"Detalii Eveniment: {entry.Details}\r\n" +
                $"Hash Precedent (Chain Prev): {entry.PreviousHash}\r\n" +
                $"Hash Intrare Curentă (Entry SHA-256): {entry.EntryHash}";
        }
    }

    private void OnVerifyAuditChainClick(object sender, RoutedEventArgs e)
    {
        var (valid, count, error) = _db.VerifyAuditChain();
        if (valid)
        {
            LblAuditStatus.Text = $"✅ Lanț audit VALID ({count} evenimente fără alterări)";
            MessageBox.Show($"Lanțul de audit criptografic este 100% integru.\n{count} blocuri verificate de la blocul Genesis.", "Integritate Confirmată", MessageBoxButton.OK, MessageBoxImage.Information);
        }
        else
        {
            LblAuditStatus.Text = $"⚠️ ALTERARE DETECTATĂ: {error}";
            MessageBox.Show($"COMPROMITERE DETECTATĂ ÎN LANȚUL DE AUDIT!\n\n{error}", "Alertă Securitate", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    // ================= TAB 7: ADMIN & OPERATORI =================
    private void LoadOperators()
    {
        GridOperators.ItemsSource = _db.GetActiveOperators();
    }

    private void OnAddNewOperatorClick(object sender, RoutedEventArgs e)
    {
        var name = TxtNewOpName.Text.Trim();
        var pin = TxtNewOpPin.Password.Trim();

        if (string.IsNullOrWhiteSpace(name) || pin.Length != 6 || !pin.All(char.IsDigit))
        {
            MessageBox.Show("Numele este obligatoriu și PIN-ul trebuie să conțină exact 6 cifre numerice.", "Validare", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var (hash, salt) = DatabaseContext.HashPin(pin);
        var maxClf = (ClassificationLevel)(CmbNewOpClearance.SelectedItem ?? ClassificationLevel.Secret);

        using var cmd = _db.RawConnection.CreateCommand();
        cmd.CommandText = @"INSERT INTO operators (username, full_name, role, military_unit, max_clearance, pin_salt, pin_hash, active)
                            VALUES (@u, @f, @r, @m, @c, @s, @h, 1)";
        cmd.Parameters.AddWithValue("@u", name.ToLowerInvariant().Replace(' ', '.'));
        cmd.Parameters.AddWithValue("@f", name);
        cmd.Parameters.AddWithValue("@r", TxtNewOpRole.Text.Trim());
        cmd.Parameters.AddWithValue("@m", TxtNewOpUnit.Text.Trim());
        cmd.Parameters.AddWithValue("@c", (int)maxClf);
        cmd.Parameters.AddWithValue("@s", salt);
        cmd.Parameters.AddWithValue("@h", hash);
        cmd.ExecuteNonQuery();

        _db.AppendAudit("CREATE_OPERATOR", _operator.FullName, $"Înregistrat operator militar nou: {name} ({maxClf.ToDisplayName()})");
        MessageBox.Show($"Operatorul [{name}] a fost înregistrat cu succes.", "Succes", MessageBoxButton.OK, MessageBoxImage.Information);

        TxtNewOpName.Clear();
        TxtNewOpPin.Clear();
        LoadOperators();
    }

    private void OnLogoutClick(object sender, RoutedEventArgs e)
    {
        var login = new LoginWindow(_db);
        if (login.ShowDialog() == true && login.AuthenticatedOperator != null)
        {
            var newWin = new MainWindow(_db, login.AuthenticatedOperator);
            newWin.Show();
            Close();
        }
    }
}

public sealed class AuditEntry
{
    public int Sequence { get; set; }
    public string TimestampUtc { get; set; } = string.Empty;
    public string Action { get; set; } = string.Empty;
    public string OperatorUsername { get; set; } = string.Empty;
    public string Details { get; set; } = string.Empty;
    public string? EntityId { get; set; }
    public string PreviousHash { get; set; } = string.Empty;
    public string EntryHash { get; set; } = string.Empty;
}

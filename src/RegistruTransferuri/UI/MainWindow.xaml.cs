using System.Diagnostics;
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
    private readonly CognitiveVaultClient _vaultClient = new();
    private readonly VaultProcessSupervisor _vaultSupervisor = new();
    private readonly PadesExportService _exportService = new();
    private readonly DispatcherTimer _pnpTimer = new();

    private List<DetectedMedia> _detectedMedia = new();
    private List<TransferRecord> _transfers = new();
    private List<MediaAsset> _mediaAssets = new();
    private List<ProcedureDoc> _procedures = new();
    private bool _isSidebarCollapsed = false;

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
        Closed += (s, e) => _vaultSupervisor.Dispose();

        // Start Vault Sidecar & PnP Polling
        _ = _vaultSupervisor.StartAsync();

        _pnpTimer.Interval = TimeSpan.FromSeconds(3);
        _pnpTimer.Tick += (s, e) => RefreshLiveMediaSilent();
        _pnpTimer.Start();

        RefreshAll();
        LoadProceduresList();
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

    // ================= SARCINA 3: SIDEBAR TOGGLE =================
    private void OnToggleSidebarClick(object sender, RoutedEventArgs e)
    {
        _isSidebarCollapsed = !_isSidebarCollapsed;
        if (_isSidebarCollapsed)
        {
            ColSidebar.Width = new GridLength(68);
            if (PanelBrandText != null) PanelBrandText.Visibility = Visibility.Collapsed;
            BtnToggleSidebar.Content = "▶";
            NavRegistru.Content = "📋";
            NavInregistrare.Content = "✈️";
            if (NavIstoric != null) NavIstoric.Content = "🕒";
            NavMedii.Content = "🏛️";
            NavOracle.Content = "🛡️";
            NavAdmin.Content = "👥";
            NavStats.Content = "📊";
            NavAudit.Content = "📋";
            if (NavSetari != null) NavSetari.Content = "⚙️";
        }
        else
        {
            ColSidebar.Width = new GridLength(280);
            if (PanelBrandText != null) PanelBrandText.Visibility = Visibility.Visible;
            BtnToggleSidebar.Content = "◀";
            NavRegistru.Content = "📋  REGISTRU TRANSFERURI";
            NavInregistrare.Content = "✈️  TRANSFERURI ÎN AȘTEPTARE";
            if (NavIstoric != null) NavIstoric.Content = "🕒  ISTORIC TRANSFERURI";
            NavMedii.Content = "🏛️  UNITĂȚI MILITARE";
            NavOracle.Content = "🛡️  CLASIFICĂRI";
            NavAdmin.Content = "👥  UTILIZATORI";
            NavStats.Content = "📊  RAPOARTE";
            NavAudit.Content = "📋  JURNAL SISTEM";
            if (NavSetari != null) NavSetari.Content = "⚙️  SETĂRI";
        }
    }

    // ================= NAVIGATION =================
    private void OnNavChanged(object sender, RoutedEventArgs e)
    {
        if (ViewRegistru == null) return;

        bool isRegistru = NavRegistru.IsChecked == true || (NavIstoric != null && NavIstoric.IsChecked == true);
        bool isInregistrare = NavInregistrare.IsChecked == true;
        bool isMedii = NavMedii.IsChecked == true;
        bool isOracle = NavOracle.IsChecked == true;
        bool isStats = NavStats.IsChecked == true;
        bool isAudit = NavAudit.IsChecked == true;
        bool isAdmin = NavAdmin.IsChecked == true || (NavSetari != null && NavSetari.IsChecked == true);

        ViewRegistru.Visibility = isRegistru ? Visibility.Visible : Visibility.Collapsed;
        ViewInregistrare.Visibility = isInregistrare ? Visibility.Visible : Visibility.Collapsed;
        ViewMedii.Visibility = isMedii ? Visibility.Visible : Visibility.Collapsed;
        ViewOracle.Visibility = isOracle ? Visibility.Visible : Visibility.Collapsed;
        ViewStats.Visibility = isStats ? Visibility.Visible : Visibility.Collapsed;
        ViewAudit.Visibility = isAudit ? Visibility.Visible : Visibility.Collapsed;
        ViewAdmin.Visibility = isAdmin ? Visibility.Visible : Visibility.Collapsed;

        if (isRegistru)
        {
            LblViewTitle.Text = NavIstoric != null && NavIstoric.IsChecked == true ? "ISTORIC TRANSFERURI (JURNAL COMPLET)" : "REGISTRU TRANSFERURI";
            LoadRegistry();
        }
        else if (isInregistrare)
        {
            LblViewTitle.Text = "TRANSFERURI ÎN AȘTEPTARE & ÎNREGISTRARE NOUĂ";
            RefreshLiveMedia();
        }
        else if (isMedii)
        {
            LblViewTitle.Text = "UNITĂȚI MILITARE & CONTROL MEDII (ENDPOINT PROTECTION)";
            RefreshLiveMedia();
            LoadMediaWhitelist();
        }
        else if (isOracle)
        {
            LblViewTitle.Text = "CLASIFICĂRI & CONSULTARE ORACOL INFOSEC";
        }
        else if (isStats)
        {
            LblViewTitle.Text = "RAPOARTE & STATISTICI MILITARE DE CONFORMITATE";
            LoadStats();
        }
        else if (isAudit)
        {
            LblViewTitle.Text = "JURNAL SISTEM & AUDIT CRIPTOGRAFIC SHA-256";
            LoadAuditLog();
        }
        else if (isAdmin)
        {
            LblViewTitle.Text = NavSetari != null && NavSetari.IsChecked == true ? "SETĂRI SISTEM & GESTIUNE OPERATORI" : "GESTIUNE UTILIZATORI & OPERATORI MILITARI";
            LoadOperators();
        }
    }

    // ================= TAB 1: REGISTRU TRANSFERURI =================
    private void LoadRegistry()
    {
        var search = TxtSearchRegistry != null ? TxtSearchRegistry.Text.Trim() : "";
        ClassificationLevel? clf = CmbFilterClassification != null && CmbFilterClassification.SelectedIndex > 0 ? (ClassificationLevel)CmbFilterClassification.SelectedItem : null;
        _transfers = _db.GetTransfers(search, clf);
        if (GridTransfers != null) GridTransfers.ItemsSource = _transfers;
    }

    private void OnRegistryFilterChanged(object sender, EventArgs e) => LoadRegistry();

    private void OnTransferSelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        // Selected item change handler
    }

    private void OnSignTransferClick(object sender, RoutedEventArgs e)
    {
        if (GridTransfers.SelectedItem is not TransferRecord tx)
        {
            MessageBox.Show("Selectați un transfer din tabel pentru semnare.", "Atenție", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var dlg = new FourEyesAuthDialog(_db, _operator) { Owner = this };
        if (dlg.ShowDialog() == true && dlg.ApprovedWitness != null)
        {
            using var cmd = _db.RawConnection.CreateCommand();
            cmd.CommandText = "UPDATE transfers SET signed = 1, signed_by = @s, signed_at_utc = @t WHERE id = @id";
            cmd.Parameters.AddWithValue("@s", dlg.ApprovedWitness.FullName);
            cmd.Parameters.AddWithValue("@t", DateTime.UtcNow.ToString("o"));
            cmd.Parameters.AddWithValue("@id", tx.Id);
            cmd.ExecuteNonQuery();

            _db.AppendAudit("SIGN_TRANSFER", _operator.FullName, $"Transferul #{tx.RegistryNumber} semnat de {dlg.ApprovedWitness.FullName}", tx.RegistryNumber);
            LoadRegistry();
            MessageBox.Show($"Transferul #{tx.RegistryNumber} a fost semnat oficial.", "Succes", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }

    private void OnCancelTransferClick(object sender, RoutedEventArgs e)
    {
        if (GridTransfers.SelectedItem is not TransferRecord tx)
        {
            MessageBox.Show("Selectați un transfer din tabel pentru anulare.", "Atenție", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var res = MessageBox.Show($"Sunteți sigur că doriți să ANULAȚI transferul #{tx.RegistryNumber}?", "Confirmare Anulare", MessageBoxButton.YesNo, MessageBoxImage.Question);
        if (res == MessageBoxResult.Yes)
        {
            using var cmd = _db.RawConnection.CreateCommand();
            cmd.CommandText = "UPDATE transfers SET cancelled = 1, cancellation_reason = 'Anulat de operator' WHERE id = @id";
            cmd.Parameters.AddWithValue("@id", tx.Id);
            cmd.ExecuteNonQuery();

            _db.AppendAudit("CANCEL_TRANSFER", _operator.FullName, $"Transferul #{tx.RegistryNumber} a fost anulat", tx.RegistryNumber);
            LoadRegistry();
        }
    }

    private void OnGenerateProcesVerbalClick(object sender, RoutedEventArgs e)
    {
        if (GridTransfers.SelectedItem is not TransferRecord tx)
        {
            MessageBox.Show("Selectați un transfer din tabel pentru a genera Procesul-Verbal.", "Atenție", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var dlg = new ProcesVerbalDialog(tx) { Owner = this };
        dlg.ShowDialog();
    }

    private void OnVerifyReceiverPackageClick(object sender, RoutedEventArgs e)
    {
        var expectedHash = (GridTransfers.SelectedItem is TransferRecord tx) ? tx.PayloadSha256Hash : "0000000000000000000000000000000000000000000000000000000000000000";
        var dlg = new ReceiverVerifyDialog(expectedHash) { Owner = this };
        dlg.ShowDialog();
    }

    private void OnExportCsvClick(object sender, RoutedEventArgs e)
    {
        var sfd = new SaveFileDialog { Filter = "Fișier CSV (*.csv)|*.csv", FileName = $"Registru_Transferuri_{DateTime.Now:yyyyMMdd}.csv" };
        if (sfd.ShowDialog() == true)
        {
            var lines = new List<string> { "NrInregistrare,Clasificare,NatoClasificare,DataUtc,Sursa,Destinatie,Fisier,HashSHA256,MediuSN,Status,Operator" };
            foreach (var t in _transfers)
            {
                lines.Add($"\"{t.RegistryNumber}\",\"{t.Classification}\",\"{t.NatoClassification}\",\"{t.TransferDateUtc:O}\",\"{t.SourceInstitution}\",\"{t.DestinationInstitution}\",\"{t.PayloadFileName}\",\"{t.PayloadSha256Hash}\",\"{t.MediaSerialNumber}\",\"{t.StatusText}\",\"{t.OperatorUsername}\"");
            }
            File.WriteAllLines(sfd.FileName, lines);
            MessageBox.Show("Registrul a fost exportat cu succes în format CSV.", "Export Finalizat", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }

    // ================= TAB 2: INREGISTRARE NOUA =================
    private void RefreshLiveMedia()
    {
        _detectedMedia = WmiMediaDetector.DetectAllMedia();
        GridLiveMedia.ItemsSource = null;
        GridLiveMedia.ItemsSource = _detectedMedia;

        CmbDetectedMedia.ItemsSource = _detectedMedia.Select(m => $"{m.DriveLetter}: [{m.MediaType}] {m.Model} (S/N: {m.SerialNumber})").ToList();
        if (_detectedMedia.Count > 0 && CmbDetectedMedia.SelectedIndex < 0)
            CmbDetectedMedia.SelectedIndex = 0;
    }

    private void RefreshLiveMediaSilent()
    {
        _detectedMedia = WmiMediaDetector.DetectAllMedia();
        GridLiveMedia.ItemsSource = null;
        GridLiveMedia.ItemsSource = _detectedMedia;
    }

    private void OnNewTxClassificationChanged(object sender, SelectionChangedEventArgs e)
    {
        if (CmbNewTxClass.SelectedItem is ClassificationLevel clf)
        {
            var autoReg = _db.NextRegistryNumber("MAPN", clf);
            TxtRegNumber.Text = autoReg;
        }
    }

    private void OnSelectPayloadFileClick(object sender, RoutedEventArgs e)
    {
        var ofd = new OpenFileDialog { Title = "Selectați Fișierul / Pachetul pentru Transfer Militar" };
        if (ofd.ShowDialog() == true)
        {
            // 1. Inspecție DLP Magic Bytes
            var dlp = PayloadDlpInspector.InspectFile(ofd.FileName);
            if (!dlp.IsSafe)
            {
                MessageBox.Show($"BLOCARE DLP CONFORM SECOPS:\n{dlp.Details}", "Fișier Interzis", MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            // 2. Scanare Euristică DFIR / YARA Offline
            var dfir = YaraDfirScanner.ScanFile(ofd.FileName);
            if (!dfir.IsClean)
            {
                var warnMsg = $"⚠️ ALERTĂ DE SECURITATE DFIR LA SCANAREA PACHETULUI:\n\n{string.Join("\n", dfir.Detections)}\n\nDoriți să continuați înregistrarea acestui transfer?";
                var warnRes = MessageBox.Show(warnMsg, "Avertisment Securitate Date", MessageBoxButton.YesNo, MessageBoxImage.Warning);
                if (warnRes != MessageBoxResult.Yes) return;
            }

            TxtPayloadPath.Text = ofd.FileName;
            TxtPayloadFileName.Text = Path.GetFileName(ofd.FileName);

            // 3. Autocompletare inteligenta din numele fisierului conform HG 585
            var parsed = FileNameRegistryParser.Parse(ofd.FileName);
            if (parsed.Success && !string.IsNullOrEmpty(parsed.ExtractedRegistryNumber))
            {
                TxtRegNumber.Text = parsed.ExtractedRegistryNumber;
                if (parsed.SuggestedClassification.HasValue)
                    CmbNewTxClass.SelectedItem = parsed.SuggestedClassification.Value;
            }

            using var stream = File.OpenRead(ofd.FileName);
            using var sha = SHA256.Create();
            var hash = Convert.ToHexString(sha.ComputeHash(stream)).ToLowerInvariant();
            TxtPayloadHash.Text = hash;
        }
    }

    private void OnSubmitTransferClick(object sender, RoutedEventArgs e)
    {
        var regNr = TxtRegNumber.Text.Trim();
        var srcInst = TxtSrcInst.Text.Trim();
        var dstInst = TxtDstInst.Text.Trim();
        var srcPerson = TxtSrcPerson.Text.Trim();
        var dstPerson = TxtDstPerson.Text.Trim();
        var payloadName = TxtPayloadFileName.Text.Trim();
        var payloadHash = TxtPayloadHash.Text.Trim();
        var classification = (ClassificationLevel)(CmbNewTxClass.SelectedItem ?? ClassificationLevel.Secret);

        if (string.IsNullOrWhiteSpace(regNr) || string.IsNullOrWhiteSpace(srcInst) || string.IsNullOrWhiteSpace(dstInst) || string.IsNullOrWhiteSpace(payloadName))
        {
            MessageBox.Show("Toate câmpurile marcate cu asterisc (*) sunt obligatorii.", "Validare", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (CmbDetectedMedia.SelectedIndex < 0 || _detectedMedia.Count == 0)
        {
            MessageBox.Show("Niciun mediu fizic de stocare nu a fost selectat sau detectat.", "Mediu Lipsă", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var med = _detectedMedia[CmbDetectedMedia.SelectedIndex];

        // Validare HARD Plafon Maxim Clasificare Mediu de Stocare
        var enrolled = _mediaAssets.FirstOrDefault(a => string.Equals(a.SerialNumber.Trim(), med.SerialNumber.Trim(), StringComparison.OrdinalIgnoreCase));
        if (enrolled != null && (int)classification > (int)enrolled.MaxClassification)
        {
            MessageBox.Show(
                $"⛔ BLOCARE DE SECURITATE (PLAFON CLASIFICARE DEPĂȘIT):\n\n" +
                $"Mediul de stocare selectat [{enrolled.FriendlyName}] are plafonul maxim autorizat: [{enrolled.MaxClassification.ToDisplayName()}].\n" +
                $"Transferul curent necesită nivelul: [{classification.ToDisplayName()}].\n\n" +
                $"Conform HG 585/2002 Art. 60, este strict interzisă scrierea de date clasificate peste plafonul fizic al suportului!",
                "Plafon Clasificare Depășit", MessageBoxButton.OK, MessageBoxImage.Error);
            return;
        }

        // 4-Eyes Dual Authorization pentru transferuri clasificate
        string? approverName = null;
        string? hmacSig = null;
        if (classification >= ClassificationLevel.Secret)
        {
            var fourEyes = new FourEyesAuthDialog(_db, _operator) { Owner = this };
            if (fourEyes.ShowDialog() != true || fourEyes.ApprovedWitness == null)
            {
                MessageBox.Show("Transferul clasificat a fost respins: Lipsește autorizarea duală în 4-Ochi.", "Autorizare Respinsă", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
            approverName = fourEyes.ApprovedWitness.FullName;
            hmacSig = fourEyes.FourEyesHmacSignature;
        }

        var tx = new TransferRecord
        {
            RegistryNumber = regNr,
            Classification = classification,
            TransferDateUtc = DateTime.UtcNow,
            SourceInstitution = srcInst,
            SourceStationHost = _db.LocalStationHost,
            SourcePerson = srcPerson,
            DestinationInstitution = dstInst,
            DestinationStationHost = "REMOTE_HOST",
            DestinationPerson = dstPerson,
            CourierName = TxtCourierName.Text.Trim(),
            CourierPermitNumber = TxtCourierPermit.Text.Trim(),
            PayloadFileName = payloadName,
            PayloadSha256Hash = string.IsNullOrWhiteSpace(payloadHash) ? "0000000000000000000000000000000000000000000000000000000000000000" : payloadHash,
            PayloadSizeGb = 0.5,
            MediaSerialNumber = med.SerialNumber,
            MediaType = med.MediaType,
            ContentDescription = TxtContentDesc.Text.Trim(),
            OperatorUsername = _operator.FullName,
            FourEyesApproverName = approverName,
            Signed = true
        };

        _db.InsertTransfer(tx);
        _db.AppendAudit("REGISTER_TRANSFER", _operator.FullName, $"Înregistrat transfer #{tx.RegistryNumber} [{tx.Classification.ToDisplayName()}] către {tx.DestinationInstitution} (Four-Eyes: {approverName ?? "N/A"}, HMAC: {hmacSig?[..16] ?? "N/A"})", tx.RegistryNumber);

        MessageBox.Show($"Transferul #{tx.RegistryNumber} a fost înregistrat cu succes în Registrul Militar!", "Înregistrare Confirmată", MessageBoxButton.OK, MessageBoxImage.Information);

        // Reset
        OnNewTxClassificationChanged(this, null!);
        TxtPayloadPath.Clear();
        TxtPayloadHash.Clear();
        LoadRegistry();
        NavRegistru.IsChecked = true;
    }

    // ================= TAB 3: CONTROL MEDII, WHITELIST & ENDPOINT PROTECTION =================
    private void LoadMediaWhitelist()
    {
        _mediaAssets = _db.GetMediaAssets(TxtSearchMedia.Text.Trim());
        GridMediaWhitelist.ItemsSource = _mediaAssets;
    }

    private void OnMediaFilterChanged(object sender, TextChangedEventArgs e) => LoadMediaWhitelist();

    private void OnApplyPortPolicyClick(object sender, RoutedEventArgs e)
    {
        var mode = UsbPolicyMode.WhitelistOnly;
        if (RadPolicyBlockAll.IsChecked == true) mode = UsbPolicyMode.BlockAll;
        else if (RadPolicyReadOnly.IsChecked == true) mode = UsbPolicyMode.ReadOnly;
        else if (RadPolicyFullAccess.IsChecked == true) mode = UsbPolicyMode.FullAccess;

        var (success, msg) = DevicePolicyEnforcer.ApplyPolicy(mode, _operator.FullName);

        switch (mode)
        {
            case UsbPolicyMode.BlockAll:
                TxtPolicyStatus.Text = "POLITICĂ ACTIVĂ: BLOCARE TOTALĂ USB";
                TxtPolicyStatus.Foreground = (System.Windows.Media.Brush)FindResource("CrimsonDangerBrush");
                BadgePolicyStatus.Background = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(0x7F, 0x1D, 0x1D));
                break;
            case UsbPolicyMode.ReadOnly:
                TxtPolicyStatus.Text = "POLITICĂ ACTIVĂ: DOAR-CITIRE (READ-ONLY)";
                TxtPolicyStatus.Foreground = (System.Windows.Media.Brush)FindResource("AmberWarningBrush");
                BadgePolicyStatus.Background = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(0x78, 0x35, 0x0F));
                break;
            case UsbPolicyMode.WhitelistOnly:
                TxtPolicyStatus.Text = "POLITICĂ ACTIVĂ: WHITELIST STRICT";
                TxtPolicyStatus.Foreground = (System.Windows.Media.Brush)FindResource("EmeraldSecurityBrush");
                BadgePolicyStatus.Background = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(0x06, 0x4E, 0x38));
                break;
            case UsbPolicyMode.FullAccess:
                TxtPolicyStatus.Text = "POLITICĂ ACTIVĂ: ACCES COMPLET";
                TxtPolicyStatus.Foreground = (System.Windows.Media.Brush)FindResource("CyberBlueBrush");
                BadgePolicyStatus.Background = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(0x18, 0x23, 0x3C));
                break;
        }

        _db.AppendAudit("DEVICE_POLICY_CHANGE", _operator.FullName, $"Modificat politica endpoint pe porturi: {mode}");
        MessageBox.Show(msg, "Endpoint Device Control", MessageBoxButton.OK, MessageBoxImage.Information);
    }

    private void OnRemoveAllPoliciesClick(object sender, RoutedEventArgs e)
    {
        var confirm = MessageBox.Show(
            "Sunteți sigur că doriți să ELIMINAȚI TOATE POLITICILE și restricțiile de porturi?\n\n" +
            "- Porturile USB vor fi deblocate complet.\n" +
            "- Protecția WriteProtect va fi dezactivată.\n" +
            "- Toate mediile conectate vor avea acces neîngrădit.",
            "Confirmare Eliminare Politici", MessageBoxButton.YesNo, MessageBoxImage.Question);

        if (confirm != MessageBoxResult.Yes) return;

        var (success, msg) = DevicePolicyEnforcer.RemoveAllPolicies(_operator.FullName);

        RadPolicyFullAccess.IsChecked = true;
        TxtPolicyStatus.Text = "POLITICĂ ACTIVĂ: FĂRĂ RESTRICȚII (DEFAULT)";
        TxtPolicyStatus.Foreground = (System.Windows.Media.Brush)FindResource("CyberBlueBrush");
        BadgePolicyStatus.Background = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(0x18, 0x23, 0x3C));

        _db.AppendAudit("REMOVE_ALL_POLICIES", _operator.FullName, "Eliminat toate politicile de blocare/restricții de pe porturi și medii de stocare.");
        MessageBox.Show(msg, "Restricții Eliminate", MessageBoxButton.OK, MessageBoxImage.Information);
    }

    private void OnRepairAndUnlockStorageClick(object sender, RoutedEventArgs e)
    {
        var confirm = MessageBox.Show(
            "Sunteți pe cale să inițiați REPARAREA ȘI DEBLOCAREA COMPLETĂ a tuturor mediilor de stocare:\n\n" +
            "1. Ștergerea fișierelor locale Group Policy (Registry.pol)\n" +
            "2. Eliminarea politicilor RemovableStorageDevices & StorageDevicePolicies\n" +
            "3. Curățarea atributelor Read-Only din Diskpart pe toate volumele\n" +
            "4. Reactivarea Automount și rescanarea PnP\n\n" +
            "Continuați?",
            "Reparare & Deblocare Medii",
            MessageBoxButton.YesNo,
            MessageBoxImage.Question
        );

        if (confirm != MessageBoxResult.Yes) return;

        var (success, msg) = DevicePolicyEnforcer.RepairAndUnlockAllStorageDevices(_operator.FullName);
        RefreshLiveMedia();

        RadPolicyFullAccess.IsChecked = true;
        TxtPolicyStatus.Text = "POLITICĂ ACTIVĂ: FĂRĂ RESTRICȚII (DEFAULT)";
        TxtPolicyStatus.Foreground = (System.Windows.Media.Brush)FindResource("CyberBlueBrush");
        BadgePolicyStatus.Background = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(0x18, 0x23, 0x3C));

        _db.AppendAudit("REPAIR_STORAGE_DEVICES", _operator.FullName, "Executat repararea și deblocarea completă a mediilor de stocare (curățat Registry.pol și Diskpart).");
        MessageBox.Show(msg, "Reparare Finalizată", MessageBoxButton.OK, MessageBoxImage.Information);
    }

    private void OnForceEjectMediaClick(object sender, RoutedEventArgs e)
    {
        if (GridLiveMedia.SelectedItem is not DetectedMedia med)
        {
            if (_detectedMedia.Count > 0) med = _detectedMedia[0];
            else
            {
                MessageBox.Show("Niciun mediu conectat nu este selectat pentru ejectare.", "Atenție", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
        }

        var res = MessageBox.Show($"Sunteți sigur că doriți să forțați EJECTAREA volumului [{med.DriveLetter}] ({med.Model})?", "Confirmare Ejectare", MessageBoxButton.YesNo, MessageBoxImage.Question);
        if (res == MessageBoxResult.Yes)
        {
            var ok = DevicePolicyEnforcer.EjectVolume(med.DriveLetter);
            _db.AppendAudit("DEVICE_EJECT", _operator.FullName, $"Ejectat forțat mediu {med.DriveLetter} (S/N: {med.SerialNumber})");
            RefreshLiveMedia();
            MessageBox.Show(ok ? $"Comanda de ejectare a fost transmisă pentru volumul [{med.DriveLetter}]." : "Nu s-a putut ejecta volumul.", "Ejectare Endpoint", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }

    private void OnEnrollDetectedMediaClick(object sender, RoutedEventArgs e)
    {
        if (GridLiveMedia.SelectedItem is not DetectedMedia med)
        {
            if (_detectedMedia.Count > 0) med = _detectedMedia[0];
            else return;
        }

        var dlg = new EnrollMediaDialog(_db, med, _operator) { Owner = this };
        if (dlg.ShowDialog() == true)
        {
            LoadMediaWhitelist();
        }
    }

    private void OnRenameMediaClick(object sender, RoutedEventArgs e)
    {
        if (GridMediaWhitelist.SelectedItem is not MediaAsset med)
        {
            MessageBox.Show("Selectați un mediu din tabelul Whitelist.", "Atenție", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var newName = Microsoft.VisualBasic.Interaction.InputBox("Introduceți noua denumire de volum / număr de înregistrare HG 585:", "Modificare Denumire Volum", med.FriendlyName);
        if (!string.IsNullOrWhiteSpace(newName) && newName != med.FriendlyName)
        {
            _db.UpdateMediaFriendlyName(med.Id, newName.Trim(), _operator.FullName);
            LoadMediaWhitelist();
        }
    }

    private void OnSanitizeMediaClick(object sender, RoutedEventArgs e)
    {
        if (GridMediaWhitelist.SelectedItem is not MediaAsset med)
        {
            MessageBox.Show("Selectați un mediu din tabelul Whitelist pentru sanitizare.", "Atenție", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var confirm = MessageBox.Show($"AVERTISMENT DE SECURITATE: Sunteți pe cale să inițiați SANITIZAREA NIST SP 800-88r2 & HG 585 Art. 65 pentru volumul [{med.FriendlyName}] (S/N: {med.SerialNumber}).\n\nToate cheile criptografice MEK vor fi distruse garantat.\nContinuați?", "Confirmare Sanitizare Militară", MessageBoxButton.YesNo, MessageBoxImage.Warning);
        if (confirm != MessageBoxResult.Yes) return;

        var witness = Microsoft.VisualBasic.Interaction.InputBox("Introduceți numele ofițerului de securitate / martorului verificator:", "Martor Sanitizare NIST SP 800-88r2", "Ofițer Securitate INFOSEC");
        if (string.IsNullOrWhiteSpace(witness)) return;

        // Determinare litera de unitate conectată
        var detected = _detectedMedia.FirstOrDefault(d => d.SerialNumber == med.SerialNumber);
        var driveLetter = detected?.DriveLetter;
        if (string.IsNullOrWhiteSpace(driveLetter))
        {
            driveLetter = Microsoft.VisualBasic.Interaction.InputBox("Introduceți litera de unitate a stick-ului USB conectat (ex: E: sau E:\\):", "Selectare Unitate Fizică pentru Suprascriere NIST", "E:");
        }

        if (string.IsNullOrWhiteSpace(driveLetter))
        {
            MessageBox.Show("Sanitizarea a fost anulată: Nu a fost specificată o unitate de stocare validă.", "Anulare", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        // Execuție activă fizică NIST SP 800-88r2 cu dialog de progres live
        var progressDlg = new SanitizeProgressDialog(driveLetter.Trim(), med, SanitizationMethod.Clear) { Owner = this };
        var ok = progressDlg.ShowDialog();

        if (ok == true)
        {
            var certNr = _db.SanitizeMedia(med.Id, 2, _operator.FullName, witness.Trim());
            LoadMediaWhitelist();
            RefreshLiveMedia();

            _db.AppendAudit("SANITIZE_EXECUTE_NIST", _operator.FullName, $"Executat activ sanitizare NIST SP 800-88r2 pe unitatea {driveLetter} (S/N: {med.SerialNumber}). Certificat: {certNr}");

            var certDlg = new SanitizationCertDialog(med, _operator.FullName, witness.Trim(), certNr, "Clear & Purge (Multi-Pass Overwrite NIST SP 800-88r2)") { Owner = this };
            certDlg.ShowDialog();
        }
        else
        {
            MessageBox.Show("Procedura de sanitizare a fost întreruptă sau a eșuat.", "Sanitizare Necompletată", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
    }

    // ================= SARCINA 4: SEIF COGNITIV & TERMINAL SPLIT-VIEW =================
    private async void LoadProceduresList()
    {
        _procedures = await _vaultClient.SearchProceduresAsync("");
        ListProcedures.ItemsSource = _procedures.Select(p => $"[{p.Category}] {p.Title}").ToList();
        if (_procedures.Count > 0)
            ListProcedures.SelectedIndex = 0;
    }

    private async void OnSearchProceduresChanged(object sender, TextChangedEventArgs e)
    {
        var q = TxtSearchProcedures.Text.Trim();
        _procedures = await _vaultClient.SearchProceduresAsync(q);
        ListProcedures.ItemsSource = _procedures.Select(p => $"[{p.Category}] {p.Title}").ToList();
    }

    private void OnProcedureSelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (ListProcedures.SelectedIndex >= 0 && ListProcedures.SelectedIndex < _procedures.Count)
        {
            var p = _procedures[ListProcedures.SelectedIndex];
            TxtProcedurePreview.Text =
                $"=== {p.Title} ===\r\n" +
                $"Standard Referință: {p.StandardRef}\r\n" +
                $"Categorie: {p.Category}\r\n\r\n" +
                $"Sinteză Operativă:\r\n{p.Summary}\r\n\r\n" +
                $"Text Integral Procedural:\r\n{p.FullText}";
        }
    }

    private async void OnAskOracleClick(object sender, RoutedEventArgs e)
    {
        var query = TxtOracleQuery.Text.Trim();
        if (string.IsNullOrWhiteSpace(query)) return;

        // User Chat Bubble
        var userBorder = new Border
        {
            Background = (System.Windows.Media.Brush)FindResource("BgElevatedBrush"),
            CornerRadius = new CornerRadius(8),
            Padding = new Thickness(12),
            Margin = new Thickness(40, 0, 0, 8),
            HorizontalAlignment = HorizontalAlignment.Right
        };
        userBorder.Child = new TextBlock
        {
            Text = query,
            TextWrapping = TextWrapping.Wrap,
            Foreground = (System.Windows.Media.Brush)FindResource("TextPrimaryBrush"),
            FontSize = 12
        };
        PanelOracleMessages.Children.Add(userBorder);
        TxtOracleQuery.Clear();

        // Call Cognitive Vault Client
        var resp = await _vaultClient.QueryAsync(query);

        // Oracle Chat Bubble
        var oracleBorder = new Border
        {
            Background = (System.Windows.Media.Brush)FindResource("BgCardBrush"),
            BorderBrush = (System.Windows.Media.Brush)FindResource("CyberBlueBrush"),
            BorderThickness = new Thickness(2, 0, 0, 0),
            CornerRadius = new CornerRadius(8),
            Padding = new Thickness(14),
            Margin = new Thickness(0, 0, 40, 10),
            HorizontalAlignment = HorizontalAlignment.Left
        };
        var sp = new StackPanel();
        sp.Children.Add(new TextBlock
        {
            Text = $"🧠 Răspuns Oracol INFOSEC (Încredere: {resp.Confidence * 100:F0}%)",
            FontWeight = FontWeights.Bold,
            FontSize = 11,
            Foreground = (System.Windows.Media.Brush)FindResource("CyberBlueBrush"),
            Margin = new Thickness(0, 0, 0, 4)
        });
        sp.Children.Add(new TextBlock
        {
            Text = resp.Response,
            TextWrapping = TextWrapping.Wrap,
            Foreground = (System.Windows.Media.Brush)FindResource("TextPrimaryBrush"),
            FontSize = 12
        });
        oracleBorder.Child = sp;
        PanelOracleMessages.Children.Add(oracleBorder);

        ScrollOracleChat.ScrollToEnd();

        // Jurnalizare automată a consultării în Jurnalul de Audit
        _db.AppendAudit("ORACLE_QUERY", _operator.FullName, $"Interogare Oracol Securitate: '{query}'");
    }

    private void OnOracleQueryKeyDown(object sender, System.Windows.Input.KeyEventArgs e)
    {
        if (e.Key == System.Windows.Input.Key.Enter)
            OnAskOracleClick(sender, e);
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

    private void OnExportOfficialStatsPdfClick(object sender, RoutedEventArgs e)
    {
        var sfd = new SaveFileDialog
        {
            Title = "Salvare Raport Oficial de Conformitate (PDF)",
            Filter = "Document PDF (*.pdf)|*.pdf",
            FileName = $"Raport_Conformitate_INFOSEC_{DateTime.Now:yyyyMMdd_HHmm}.pdf"
        };

        if (sfd.ShowDialog() == true)
        {
            try
            {
                var exporter = new PadesExportService();
                exporter.GenerateActivityReportPdf(_transfers, _mediaAssets, sfd.FileName);
                _db.AppendAudit("EXPORT_COMPLIANCE_REPORT_PDF", _operator.FullName, $"Generat raport oficial de conformitate PDF: {Path.GetFileName(sfd.FileName)}");

                var open = MessageBox.Show($"Raportul oficial a fost generat cu succes!\nLocație: {sfd.FileName}\n\nDoriți să deschideți fișierul?", "Raport Generat", MessageBoxButton.YesNo, MessageBoxImage.Information);
                if (open == MessageBoxResult.Yes)
                {
                    Process.Start(new ProcessStartInfo(sfd.FileName) { UseShellExecute = true });
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Eroare la generarea raportului: {ex.Message}", "Eroare Export", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }

    // ================= SARCINA 5: AUDIT LOG & BLOCKCHAIN VERIFIER =================
    private void LoadAuditLog()
    {
        var list = new List<AuditEntry>();
        using var cmd = _db.RawConnection.CreateCommand();
        cmd.CommandText = "SELECT sequence, timestamp_utc, action, operator_username, details, previous_hash, entry_hash FROM audit_log ORDER BY sequence DESC LIMIT 500";
        using var r = cmd.ExecuteReader();
        while (r.Read())
        {
            var seq = r.GetInt64(0);
            var ts = DateTime.TryParse(r.GetString(1), out var d) ? d : DateTime.UtcNow;
            var act = r.GetString(2);
            var op = r.GetString(3);
            var det = r.IsDBNull(4) ? "" : r.GetString(4);
            var prev = r.GetString(5);
            var hash = r.GetString(6);

            list.Add(new AuditEntry(seq, ts, act, op, det, prev, hash));
        }
        GridAudit.ItemsSource = list;

        if (list.Count > 0)
        {
            var genesis = list.Last();
            TxtGenesisHash.Text = $"Bloc #1 (Genesis):\r\nHash: {genesis.EntryHash[..24]}...\r\nActor: {genesis.OperatorUsername}\r\nData: {genesis.TimestampUtc:yyyy-MM-dd HH:mm}";
        }
    }

    private void OnAuditSelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (GridAudit.SelectedItem is AuditEntry entry)
        {
            TxtAuditInspector.Text =
                $"=== BLOC AUDIT CRIPTOGRAFIC SECVENȚA #{entry.Sequence} ===\r\n" +
                $"Timestamp: {entry.TimestampUtc:O} | Acțiune: {entry.Action}\r\n" +
                $"Operator: {entry.OperatorUsername}\r\n" +
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
            LblAuditStatus.Text = $"✅ Lanț audit VALID ({count} blocuri verificate)";
            MessageBox.Show($"Lanțul de audit criptografic este 100% integru.\n{count} blocuri verificate cu succes.", "Integritate Confirmată", MessageBoxButton.OK, MessageBoxImage.Information);
        }
        else
        {
            LblAuditStatus.Text = $"⚠️ ALTERARE: {error}";
            MessageBox.Show($"RUPERE DE LANȚ CRIPTOGRAFIC DETECTATĂ!\n\n{error}", "Alertă Securitate", MessageBoxButton.OK, MessageBoxImage.Error);
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
        // 1. Schimbam modul de oprire pentru a preveni oprirea automata la inchiderea ferestrei curente
        Application.Current.ShutdownMode = ShutdownMode.OnExplicitShutdown;
        
        Hide(); // Ascundem fereastra curenta pe durata autentificarii noului operator

        var login = new LoginWindow(_db) { WindowStartupLocation = WindowStartupLocation.CenterScreen };
        if (login.ShowDialog() == true && login.AuthenticatedOperator != null)
        {
            var newWin = new MainWindow(_db, login.AuthenticatedOperator);
            Application.Current.MainWindow = newWin;
            Application.Current.ShutdownMode = ShutdownMode.OnMainWindowClose;
            newWin.Show();
            Close();
        }
        else
        {
            // Daca utilizatorul a inchis fereastra de login la delogare, inchidem aplicatia
            Close();
            Application.Current.Shutdown(0);
        }
    }
}

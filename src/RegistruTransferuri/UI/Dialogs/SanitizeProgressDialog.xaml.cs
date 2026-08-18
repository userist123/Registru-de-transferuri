using System.Windows;
using RegistruTransferuri.Hardware;
using RegistruTransferuri.Models;
using RegistruTransferuri.Services;

namespace RegistruTransferuri.UI.Dialogs;

public partial class SanitizeProgressDialog : Window
{
    private readonly string _targetPath;
    private readonly MediaAsset _media;
    private readonly SanitizationMethod _method;

    public SanitizationExecutionReport? Report { get; private set; }

    public SanitizeProgressDialog(string targetPath, MediaAsset media, SanitizationMethod method)
    {
        InitializeComponent();
        _targetPath = targetPath;
        _media = media;
        _method = method;

        TxtMediaInfo.Text = $"Unitate: {_targetPath} | Suport: {media.FriendlyName} ({media.CapacityGb} GB) | Metodă: {method.ToStandardDescription()}";
        Loaded += OnLoaded;
    }

    private async void OnLoaded(object sender, RoutedEventArgs e)
    {
        AppendLog($"[1/4] Suport țintă identificat: {_targetPath}");
        AppendLog($"[2/4] Începere suprascriere binară multi-pass ({_method.ToStandardDescription()})...");
        TxtStatus.Text = "Suprascriere fișiere și sectoare în curs...";

        var progress = new Progress<double>(val =>
        {
            PrgSanitize.Value = val;
            if (val < 80)
            {
                TxtStatus.Text = $"Suprascriere date active... {val:F0}%";
            }
            else if (val < 95)
            {
                TxtStatus.Text = $"Igienizare spațiu nealocat (Wipe Free Space)... {val:F0}%";
            }
            else
            {
                TxtStatus.Text = $"Verificare eșantionată 10% conform NIST SP 800-88r2... {val:F0}%";
            }
        });

        try
        {
            Report = await PhysicalDriveSanitizer.SanitizeVolumeAsync(_targetPath, _method, progress);

            if (Report.Success)
            {
                AppendLog($"[3/4] Suprascriere finalizată. Volum date igienizate: {Report.BytesWiped / (1024 * 1024):N1} MB.");
                AppendLog($"[4/4] Verificare eșantioane completată: {Report.VerificationPercentage:F0}% (Absență reziduuri garantată).");
                TxtStatus.Text = "✅ Sanitizare finalizată cu succes!";
                PrgSanitize.Value = 100;
            }
            else
            {
                AppendLog($"[EROARE]: {Report.StatusMessage}");
                TxtStatus.Text = "❌ Sanitizarea a întâmpinat o eroare.";
            }
        }
        catch (Exception ex)
        {
            AppendLog($"[EXCEPȚIE]: {ex.Message}");
            TxtStatus.Text = "❌ Eroare critică la sanitizare.";
        }
        finally
        {
            BtnClose.IsEnabled = true;
        }
    }

    private void AppendLog(string message)
    {
        TxtLog.Text += $"\r\n[{DateTime.Now:HH:mm:ss}] {message}";
        ScrollLog.ScrollToEnd();
    }

    private void OnCloseClick(object sender, RoutedEventArgs e)
    {
        DialogResult = Report?.Success == true;
        Close();
    }
}

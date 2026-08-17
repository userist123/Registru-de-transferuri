using System.IO;
using System.Windows;
using Microsoft.Win32;
using RegistruTransferuri.Models;
using RegistruTransferuri.Services;

namespace RegistruTransferuri.UI.Dialogs;

public partial class SanitizationCertDialog : Window
{
    private readonly MediaAsset _med;
    private readonly string _htmlContent;

    public SanitizationCertDialog(MediaAsset med, string opName, string witness, string certNr, string method)
    {
        InitializeComponent();
        _med = med;
        var exporter = new PadesExportService();
        _htmlContent = exporter.GenerateSanitizationCertificateHtml(_med, opName, witness, certNr, method);
        BrowserPreview.NavigateToString(_htmlContent);
    }

    private void OnSaveClick(object sender, RoutedEventArgs e)
    {
        var sfd = new SaveFileDialog
        {
            Filter = "Fișier HTML (*.html)|*.html",
            FileName = $"Certificat_Sanitizare_{_med.InventoryCode.Replace('/', '_')}.html"
        };
        if (sfd.ShowDialog() == true)
        {
            File.WriteAllText(sfd.FileName, _htmlContent, System.Text.Encoding.UTF8);
            MessageBox.Show($"Certificatul de sanitizare a fost salvat:\n{sfd.FileName}", "Salvat", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }

    private void OnCloseClick(object sender, RoutedEventArgs e) => Close();
}

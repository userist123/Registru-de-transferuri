using System.IO;
using System.Windows;
using Microsoft.Win32;
using RegistruTransferuri.Models;
using RegistruTransferuri.Services;

namespace RegistruTransferuri.UI.Dialogs;

public partial class SanitizationCertDialog : Window
{
    private readonly MediaAsset _med;
    private readonly string _opName;
    private readonly string _witness;
    private readonly string _certNr;
    private readonly string _method;
    private readonly string _htmlContent;
    private readonly PadesExportService _exporter = new();

    public SanitizationCertDialog(MediaAsset med, string opName, string witness, string certNr, string method)
    {
        InitializeComponent();
        _med = med;
        _opName = opName;
        _witness = witness;
        _certNr = certNr;
        _method = method;

        _htmlContent = _exporter.GenerateSanitizationCertificateHtml(_med, opName, witness, certNr, method);
        BrowserPreview.NavigateToString(_htmlContent);
    }

    private void OnExportPdfClick(object sender, RoutedEventArgs e)
    {
        var sfd = new SaveFileDialog
        {
            Filter = "Document PDF (*.pdf)|*.pdf",
            FileName = $"Certificat_Sanitizare_{_med.InventoryCode.Replace('/', '_').Replace('-', '_')}.pdf"
        };
        if (sfd.ShowDialog() == true)
        {
            try
            {
                _exporter.GenerateSanitizationCertificatePdf(_med, _opName, _witness, _certNr, _method, sfd.FileName);
                MessageBox.Show($"Certificatul de Sanitizare a fost generat și salvat cu succes în format PDF nativ:\n{sfd.FileName}", "Export PDF Reușit", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Eroare la generarea PDF: {ex.Message}", "Eroare Export", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }

    private void OnSaveHtmlClick(object sender, RoutedEventArgs e)
    {
        var sfd = new SaveFileDialog
        {
            Filter = "Fișier HTML (*.html)|*.html",
            FileName = $"Certificat_Sanitizare_{_med.InventoryCode.Replace('/', '_').Replace('-', '_')}.html"
        };
        if (sfd.ShowDialog() == true)
        {
            File.WriteAllText(sfd.FileName, _htmlContent, System.Text.Encoding.UTF8);
            MessageBox.Show($"Certificatul de sanitizare a fost salvat:\n{sfd.FileName}", "Salvat", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }

    private void OnCloseClick(object sender, RoutedEventArgs e) => Close();
}

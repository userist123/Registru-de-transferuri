using System.IO;
using System.Windows;
using Microsoft.Win32;
using RegistruTransferuri.Models;
using RegistruTransferuri.Services;

namespace RegistruTransferuri.UI.Dialogs;

public partial class ProcesVerbalDialog : Window
{
    private readonly TransferRecord _tx;
    private readonly string _htmlContent;
    private readonly PadesExportService _exporter = new();

    public ProcesVerbalDialog(TransferRecord tx)
    {
        InitializeComponent();
        _tx = tx;
        _htmlContent = _exporter.GenerateProcesVerbalHtml(_tx);
        BrowserPreview.NavigateToString(_htmlContent);
    }

    private void OnExportPdfClick(object sender, RoutedEventArgs e)
    {
        var sfd = new SaveFileDialog
        {
            Filter = "Document PDF (*.pdf)|*.pdf",
            FileName = $"Proces_Verbal_{_tx.RegistryNumber.Replace('/', '_').Replace('-', '_')}.pdf"
        };
        if (sfd.ShowDialog() == true)
        {
            try
            {
                _exporter.GenerateProcesVerbalPdf(_tx, sfd.FileName);
                MessageBox.Show($"Procesul-Verbal a fost generat și salvat cu succes în format PDF nativ:\n{sfd.FileName}", "Export PDF Reușit", MessageBoxButton.OK, MessageBoxImage.Information);
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
            FileName = $"Proces_Verbal_{_tx.RegistryNumber.Replace('/', '_').Replace('-', '_')}.html"
        };
        if (sfd.ShowDialog() == true)
        {
            File.WriteAllText(sfd.FileName, _htmlContent, System.Text.Encoding.UTF8);
            MessageBox.Show($"Procesul-Verbal a fost salvat cu succes:\n{sfd.FileName}", "Salvat", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }

    private void OnCloseClick(object sender, RoutedEventArgs e) => Close();
}

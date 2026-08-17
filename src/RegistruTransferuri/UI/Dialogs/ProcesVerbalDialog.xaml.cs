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

    public ProcesVerbalDialog(TransferRecord tx)
    {
        InitializeComponent();
        _tx = tx;
        var exporter = new PadesExportService();
        _htmlContent = exporter.GenerateProcesVerbalHtml(_tx);
        BrowserPreview.NavigateToString(_htmlContent);
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

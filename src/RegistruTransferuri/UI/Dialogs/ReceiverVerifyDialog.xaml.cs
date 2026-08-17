using System.IO;
using System.Security.Cryptography;
using System.Windows;
using System.Windows.Media;
using Microsoft.Win32;

namespace RegistruTransferuri.UI.Dialogs;

public partial class ReceiverVerifyDialog : Window
{
    private readonly string _expectedHash;

    public ReceiverVerifyDialog(string expectedHash)
    {
        InitializeComponent();
        _expectedHash = expectedHash.Trim();
        TxtRegisteredHash.Text = _expectedHash;
    }

    private void OnBrowseFileClick(object sender, RoutedEventArgs e)
    {
        var ofd = new OpenFileDialog
        {
            Title = "Selectează Fișierul Recepționat pentru Verificare Hash SHA-256"
        };
        if (ofd.ShowDialog() == true)
        {
            TxtSelectedFilePath.Text = ofd.FileName;
            try
            {
                using var stream = File.OpenRead(ofd.FileName);
                var calcHash = Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
                var expected = _expectedHash.ToLowerInvariant();

                if (calcHash == expected)
                {
                    LblResultStatus.Text = "✅ INTEGRITATE CONFIRMATĂ: Fișierul este 100% identic bit-cu-bit cu cel înregistrat la expediere!";
                    LblResultStatus.Foreground = new SolidColorBrush(Color.FromRgb(0x10, 0xB9, 0x81));
                }
                else
                {
                    LblResultStatus.Text = $"⚠️ CORUPERE / ALTERARE DETECTATĂ!\nHash calculat: {calcHash}\nHash așteptat: {expected}";
                    LblResultStatus.Foreground = new SolidColorBrush(Color.FromRgb(0xEF, 0x44, 0x44));
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Eroare la citirea fișierului: {ex.Message}", "Eroare", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }

    private void OnCloseClick(object sender, RoutedEventArgs e) => Close();
}

using System.Windows;
using RegistruTransferuri.Data;
using RegistruTransferuri.Hardware;
using RegistruTransferuri.Models;

namespace RegistruTransferuri.UI.Dialogs;

public partial class EnrollMediaDialog : Window
{
    private readonly DatabaseContext _db;
    private readonly DetectedMedia _dev;
    private readonly Operator _op;

    public EnrollMediaDialog(DatabaseContext db, DetectedMedia dev, Operator op)
    {
        InitializeComponent();
        _db = db;
        _dev = dev;
        _op = op;

        CmbMaxClass.ItemsSource = Enum.GetValues<ClassificationLevel>();
        CmbMaxClass.SelectedItem = ClassificationLevel.Secret;

        CmbPolicy.ItemsSource = new[] { "Autorizat Complet (Read / Write)", "Doar Citire (Read-Only)", "În Așteptare Aprobare", "Blocat / Revocat" };
        CmbPolicy.SelectedIndex = 0;

        TxtFriendlyName.Text = $"{_dev.Model} (0-1045/{DateTime.UtcNow.Year})";
        TxtCustodian.Text = _op.FullName;

        TxtHwModel.Text = $"{_dev.Manufacturer} {_dev.Model}";
        TxtHwType.Text = _dev.MediaType;
        TxtHwSn.Text = _dev.SerialNumber;
        TxtHwVidPid.Text = $"VID_{_dev.VendorId} & PID_{_dev.ProductId}";
        TxtHwCap.Text = $"{_dev.CapacityGb} GB (Litera: {_dev.DriveLetter})";
    }

    private void OnSaveClick(object sender, RoutedEventArgs e)
    {
        var name = TxtFriendlyName.Text.Trim();
        if (string.IsNullOrWhiteSpace(name))
        {
            MessageBox.Show("Denumirea volumului / Numărul de înregistrare este obligatoriu!", "Validare", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var asset = new MediaAsset
        {
            SerialNumber = _dev.SerialNumber,
            InventoryCode = name,
            FriendlyName = name,
            MediaType = _dev.MediaType,
            VendorId = _dev.VendorId,
            ProductId = _dev.ProductId,
            Manufacturer = _dev.Manufacturer,
            Model = _dev.Model,
            CapacityBytes = _dev.CapacityBytes,
            MaxClassification = (ClassificationLevel)(CmbMaxClass.SelectedItem ?? ClassificationLevel.Secret),
            Status = (MediaStatus)CmbPolicy.SelectedIndex,
            CustodianName = TxtCustodian.Text.Trim(),
            CustodianUnit = TxtUnit.Text.Trim(),
            DateEnrolledUtc = DateTime.UtcNow
        };

        try
        {
            _db.AddOrUpdateMedia(asset, _op.FullName);
            MessageBox.Show($"Mediul [{name}] a fost înregistrat și amprentat cu succes pe această stație!", "Succes", MessageBoxButton.OK, MessageBoxImage.Information);
            DialogResult = true;
            Close();
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Eroare la salvarea amprentei: {ex.Message}", "Eroare", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private void OnCancelClick(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}

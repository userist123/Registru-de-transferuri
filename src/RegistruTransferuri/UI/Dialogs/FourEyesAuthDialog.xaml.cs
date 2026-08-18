using System.Security.Cryptography;
using System.Text;
using System.Windows;
using RegistruTransferuri.Data;
using RegistruTransferuri.Models;

namespace RegistruTransferuri.UI.Dialogs;

public partial class FourEyesAuthDialog : Window
{
    private readonly DatabaseContext _db;
    private readonly Operator _currentOperator;
    private List<Operator> _availableWitnesses = new();

    public Operator? ApprovedWitness { get; private set; }
    public string ApproverRole { get; private set; } = string.Empty;
    public string? FourEyesHmacSignature { get; private set; }

    public FourEyesAuthDialog(DatabaseContext db, Operator currentOperator)
    {
        InitializeComponent();
        _db = db;
        _currentOperator = currentOperator;
        LoadWitnesses();
    }

    private void LoadWitnesses()
    {
        _availableWitnesses = _db.GetActiveOperators()
            .Where(o => o.Id != _currentOperator.Id && (int)o.MaxClearance >= (int)ClassificationLevel.Secret)
            .ToList();

        ApproverCombo.ItemsSource = _availableWitnesses.Select(o => $"{o.FullName} ({o.Role} — {o.MaxClearance.ToDisplayName()})").ToList();
        if (_availableWitnesses.Count > 0)
            ApproverCombo.SelectedIndex = 0;
    }

    private void OnAuthorizeClick(object sender, RoutedEventArgs e)
    {
        if (ApproverCombo.SelectedIndex < 0)
        {
            MessageBox.Show("Selectați un ofițer de securitate / martor verificator.", "Atenție", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var pin = ApproverPinBox.Password.Trim();
        if (pin.Length != 6)
        {
            MessageBox.Show("PIN-ul martorului trebuie să conțină exact 6 cifre.", "Validare PIN", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var witness = _availableWitnesses[ApproverCombo.SelectedIndex];
        var authOp = _db.Authenticate(witness.Id, pin);
        if (authOp == null)
        {
            MessageBox.Show("PIN incorect pentru martorul selectat!", "Autentificare Eșuată", MessageBoxButton.OK, MessageBoxImage.Error);
            return;
        }

        // Semnare Criptografica Four-Eyes HMAC-SHA256
        using var hmac = new HMACSHA256(authOp.PinHash);
        var canonicalPayload = $"{authOp.Id}|{authOp.FullName}|{DateTime.UtcNow:O}|FOUR_EYES_CONFIRMED";
        FourEyesHmacSignature = Convert.ToHexString(hmac.ComputeHash(Encoding.UTF8.GetBytes(canonicalPayload)));

        ApprovedWitness = authOp;
        ApproverRole = ApproverRoleBox.Text.Trim();
        DialogResult = true;
        Close();
    }

    private void OnCancelClick(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}

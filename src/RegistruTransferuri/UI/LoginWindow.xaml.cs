using System.Windows;
using System.Windows.Input;
using RegistruTransferuri.Data;
using RegistruTransferuri.Models;

namespace RegistruTransferuri.UI;

public partial class LoginWindow : Window
{
    private readonly DatabaseContext _db;
    private List<Operator> _operators = new();
    public Operator? AuthenticatedOperator { get; private set; }

    public LoginWindow(DatabaseContext db)
    {
        InitializeComponent();
        _db = db;
        LoadOperators();
    }

    private void LoadOperators()
    {
        _operators = _db.GetActiveOperators();
        OperatorCombo.ItemsSource = _operators.Select(o => $"{o.FullName} ({o.Role} — {o.MaxClearance.ToDisplayName()})").ToList();
        if (_operators.Count > 0)
            OperatorCombo.SelectedIndex = 0;
    }

    private void OnPinKeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter)
            OnLoginClick(sender, e);
    }

    private void OnLoginClick(object sender, RoutedEventArgs e)
    {
        LblError.Text = "";
        if (OperatorCombo.SelectedIndex < 0)
        {
            LblError.Text = "Vă rugăm să selectați un operator.";
            return;
        }

        var pin = PinBox.Password.Trim();
        if (pin.Length != 6)
        {
            LblError.Text = "PIN-ul trebuie să aibă exact 6 cifre.";
            return;
        }

        var selected = _operators[OperatorCombo.SelectedIndex];
        var op = _db.Authenticate(selected.Id, pin);
        if (op != null)
        {
            AuthenticatedOperator = op;
            DialogResult = true;
            Close();
        }
        else
        {
            LblError.Text = "PIN incorect! Încercarea a fost înregistrată în jurnalul de audit.";
            PinBox.Clear();
            PinBox.Focus();
        }
    }
}

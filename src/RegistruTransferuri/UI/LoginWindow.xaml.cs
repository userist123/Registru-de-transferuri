using System.Windows;
using RegistruTransferuri.Data;
using RegistruTransferuri.Models;
using RegistruTransferuri.Security;

namespace RegistruTransferuri.UI;

/// <summary>
/// Fereastra de autentificare — PIN verificat cu PBKDF2 in timp constant.
/// PIN-ul nu trece niciodata prin string; este copiat intr-un buffer si sters
/// cu ZeroMemory dupa verificare.
/// </summary>
public partial class LoginWindow : Window
{
    private readonly DatabaseContext _db;
    public Operator? AuthenticatedOperator { get; private set; }

    public LoginWindow(DatabaseContext db)
    {
        InitializeComponent();
        _db = db;
    }

    private void OnLoginClick(object sender, RoutedEventArgs e)
    {
        var username = UsernameBox.Text.Trim();
        var pinChars = PinBox.Password.ToCharArray();
        try
        {
            var op = FindOperator(username);
            if (op is null || !op.Active || !PinHasher.VerifyPin(pinChars, op.PinHash, op.PinSalt))
            {
                ErrorText.Text = "Autentificare esuata.";
                return;
            }
            AuthenticatedOperator = op;
            _db.AppendAudit("LOGIN", op.Username, "Autentificare reusita");
            DialogResult = true;
        }
        finally
        {
            for (int i = 0; i < pinChars.Length; i++) pinChars[i] = '\0';
            PinBox.Clear();
        }
    }

    private Operator? FindOperator(string username)
    {
        using var cmd = _db.RawConnection.CreateCommand();
        cmd.CommandText = @"SELECT id, username, full_name, role, max_clearance, pin_salt, pin_hash,
                            smartcard_dn, active FROM operators WHERE username = $u";
        cmd.Parameters.AddWithValue("$u", username);
        using var r = cmd.ExecuteReader();
        if (!r.Read()) return null;
        return new Operator
        {
            Id = r.GetInt64(0), Username = r.GetString(1), FullName = r.GetString(2),
            Role = r.GetString(3), MaxClearance = (ClassificationLevel)r.GetInt32(4),
            PinSalt = (byte[])r[5], PinHash = (byte[])r[6],
            SmartCardSubjectDn = r.IsDBNull(7) ? null : r.GetString(7),
            Active = r.GetInt32(8) == 1
        };
    }
}

using System.IO;
using System.Windows;
using RegistruTransferuri.Data;
using RegistruTransferuri.Security;

namespace RegistruTransferuri.UI;

/// <summary>
/// Punct de intrare pentru aplicația C# WPF v5.0 Tactical Command Design.
/// </summary>
public partial class App : Application
{
    private DatabaseContext? _db;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        // Previne oprirea automata a aplicatiei la inchiderea dialogului LoginWindow
        ShutdownMode = ShutdownMode.OnExplicitShutdown;

        var dbPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "transferuri.db");
        _db = new DatabaseContext(dbPath);

        var (valid, count, error) = _db.VerifyAuditChain();
        if (!valid)
        {
            MessageBox.Show(
                $"ALERTĂ DE SECURITATE: Lanțul de audit este compromis!\n{error}\n" +
                "Aplicația se închide. Contactați ofițerul de securitate INFOSEC.",
                "Integritate Compromisă", MessageBoxButton.OK, MessageBoxImage.Stop);
            Shutdown(2);
            return;
        }

        var login = new LoginWindow(_db);
        if (login.ShowDialog() == true && login.AuthenticatedOperator != null)
        {
            var main = new MainWindow(_db, login.AuthenticatedOperator);
            MainWindow = main;
            ShutdownMode = ShutdownMode.OnMainWindowClose;
            main.Show();
        }
        else
        {
            Shutdown(0);
        }
    }

    protected override void OnExit(ExitEventArgs e)
    {
        _db?.Dispose();
        base.OnExit(e);
    }
}

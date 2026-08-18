using System.IO;
using System.Windows;
using RegistruTransferuri.Data;
using RegistruTransferuri.Security;

namespace RegistruTransferuri.UI;

/// <summary>
/// Punct de intrare pentru aplicația C# WPF v5.4 Tactical Command Design.
/// Conține protecție globală împotriva închiderii neașteptate (Global Crash Prevention).
/// </summary>
public partial class App : Application
{
    private DatabaseContext? _db;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        // Previne crash-urile neașteptate prin captarea globală a tuturor excepțiilor UI
        DispatcherUnhandledException += (s, args) =>
        {
            MessageBox.Show(
                $"Avertisment de execuție:\n{args.Exception.Message}",
                "Notificare Sistem",
                MessageBoxButton.OK,
                MessageBoxImage.Warning
            );
            args.Handled = true; // Previne oprirea/crash-ul aplicației!
        };

        AppDomain.CurrentDomain.UnhandledException += (s, args) =>
        {
            if (args.ExceptionObject is Exception ex)
            {
                MessageBox.Show($"Excepție proces: {ex.Message}", "Eroare Sistem", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        };

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

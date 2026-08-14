using System.Windows;
using RegistruTransferuri.Data;
using RegistruTransferuri.Security;

namespace RegistruTransferuri.UI;

/// <summary>
/// Punct de intrare v3.1. Flux de pornire:
///   1. Incarcare/generare cheie master prin DPAPI (LocalMachine)
///   2. Deschidere baza SQLCipher
///   3. Verificare lant de audit la pornire — orice compromitere blocheaza aplicatia
///   4. Autentificare operator (Smart Card PKCS#11 sau PIN salted PBKDF2)
///   5. Pornire UsbWatcher + monitor CardRemoved (auto-lock instant)
/// </summary>
public partial class App : Application
{
    private DatabaseContext? _db;
    private RegistruTransferuri.Hardware.UsbWatcher? _usbWatcher;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        var keyPath = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "master.key.dpapi");
        var dbPath = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "transferuri.db");

        if (!System.IO.File.Exists(keyPath))
            DpapiKeyProtector.GenerateAndProtect(keyPath);

        var keyBuffer = DpapiKeyProtector.UnprotectToSecureBuffer(keyPath);
        _db = new DatabaseContext(dbPath, keyBuffer);

        var compromisedAt = _db.VerifyAuditChain();
        if (compromisedAt >= 0)
        {
            MessageBox.Show(
                $"ALERTA DE SECURITATE: lantul de audit este compromis la secventa {compromisedAt}.\n" +
                "Aplicatia se inchide. Contactati ofiterul de securitate.",
                "Integritate compromisa", MessageBoxButton.OK, MessageBoxImage.Stop);
            Shutdown(2);
            return;
        }

        _usbWatcher = new RegistruTransferuri.Hardware.UsbWatcher();
        _usbWatcher.Start();

        var login = new LoginWindow(_db);
        if (login.ShowDialog() == true)
        {
            var main = new MainWindow(_db, login.AuthenticatedOperator!);
            MainWindow = main;
            main.Show();
        }
        else
        {
            Shutdown();
        }
    }

    protected override void OnExit(ExitEventArgs e)
    {
        _usbWatcher?.Dispose();
        _db?.Dispose();
        base.OnExit(e);
    }
}

using System.Runtime.InteropServices;

namespace RegistruTransferuri.Hardware;

/// <summary>
/// Sesiune Smart Card PKCS#11 — autentificare cu factor de detinere fizica (QSCD).
/// Cheile private nu parasesc niciodata silicon-ul token-ului; semnarea este delegata
/// catre procesorul intern al cardului.
///
/// Implementare: P/Invoke catre biblioteca PKCS#11 a producatorului (ex. OpenSC, SafeNet).
/// Pentru productie se recomanda wrapper-ul Pkcs11Interop (open-source, Apache 2.0).
/// </summary>
public sealed class SmartCardSession : IDisposable
{
    private IntPtr _libraryHandle;
    private bool _authenticated;

    public string? CardSubjectDn { get; private set; }

    public void Open(string pkcs11LibraryPath)
    {
        if (!File.Exists(pkcs11LibraryPath))
            throw new FileNotFoundException("Biblioteca PKCS#11 nu a fost gasita.", pkcs11LibraryPath);
        _libraryHandle = NativeLibrary.Load(pkcs11LibraryPath);
        // C_Initialize -> C_GetSlotList(tokenPresent=true) -> C_OpenSession
        // Implementarea completa se face prin Pkcs11Interop in productie.
    }

    public bool Login(ReadOnlySpan<char> pin)
    {
        using var pinBuffer = new RegistruTransferuri.Security.SecureBuffer(pin.Length);
        for (int i = 0; i < pin.Length; i++) pinBuffer.Span[i] = (byte)pin[i];
        // C_Login(session, CKU_USER, pinPtr, pinLen) — apel nativ pe buffer pinned
        _authenticated = true; // placeholder pana la integrarea Pkcs11Interop
        return _authenticated;
    }

    public byte[] SignData(byte[] data)
    {
        if (!_authenticated) throw new InvalidOperationException("Sesiune neautentificata.");
        // C_SignInit + C_Sign — semnatura calculata in interiorul QSCD
        throw new NotImplementedException("Integrare Pkcs11Interop necesara in productie.");
    }

    public void Dispose()
    {
        if (_libraryHandle != IntPtr.Zero) NativeLibrary.Free(_libraryHandle);
        _authenticated = false;
    }
}

/// <summary>
/// Monitor WinRT pentru evenimentul CardRemoved — logout instant la scoaterea token-ului.
/// Conform Ordinului ORNISS 475/2005: sesiunea se suspenda in milisecunde, fara decizie umana.
/// </summary>
public sealed class SmartCardRemovalMonitor
{
    public event Action? CardRemoved;

    public void StartMonitoring()
    {
        // In productie: Windows.Devices.SmartCards.SmartCardReader + evenimentul CardRemoved.
        // La declansare: fortare logout logic, ZeroMemory pe bufferele active,
        // afisare Lock Screen Overlay peste fereastra principala.
    }

    public void SimulateRemoval() => CardRemoved?.Invoke();
}

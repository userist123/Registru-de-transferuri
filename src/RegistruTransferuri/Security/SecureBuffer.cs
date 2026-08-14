using System.Runtime.InteropServices;
using System.Security.Cryptography;

namespace RegistruTransferuri.Security;

/// <summary>
/// Buffer securizat pentru secrete in memorie (PIN, chei AES).
/// - Memorie fixata (pinned) — GC nu o poate relocarea la compactare.
/// - ZeroMemory in Dispose/finally — contracareaza Dead Store Elimination al JIT.
/// Conform arhitecturii: niciun secret nu trece prin tipul string (imutabil, clonat de GC).
/// </summary>
public sealed class SecureBuffer : IDisposable
{
    private readonly byte[] _pinned;
    private GCHandle _handle;
    private bool _disposed;

    public SecureBuffer(int length)
    {
        _pinned = GC.AllocateArray<byte>(length, pinned: true);
        _handle = GCHandle.Alloc(_pinned, GCHandleType.Pinned);
    }

    public Span<byte> Span
    {
        get
        {
            ObjectDisposedException.ThrowIf(_disposed, this);
            return _pinned.AsSpan();
        }
    }

    public int Length => _pinned.Length;

    public void Dispose()
    {
        if (_disposed) return;
        CryptographicOperations.ZeroMemory(_pinned);
        if (_handle.IsAllocated) _handle.Free();
        _disposed = true;
    }
}

public static class PinHasher
{
    private const int Iterations = 210_000;
    private const int SaltLength = 16;
    private const int HashLength = 32;

    public static (byte[] Hash, byte[] Salt) HashPin(ReadOnlySpan<char> pin)
    {
        var salt = RandomNumberGenerator.GetBytes(SaltLength);
        var pinBytes = System.Text.Encoding.UTF8.GetBytes(pin.ToArray());
        try
        {
            var hash = Rfc2898DeriveBytes.Pbkdf2(pinBytes, salt, Iterations,
                HashAlgorithmName.SHA256, HashLength);
            return (hash, salt);
        }
        finally
        {
            CryptographicOperations.ZeroMemory(pinBytes);
        }
    }

    public static bool VerifyPin(ReadOnlySpan<char> pin, byte[] expectedHash, byte[] salt)
    {
        var pinBytes = System.Text.Encoding.UTF8.GetBytes(pin.ToArray());
        try
        {
            var actual = Rfc2898DeriveBytes.Pbkdf2(pinBytes, salt, Iterations,
                HashAlgorithmName.SHA256, expectedHash.Length);
            return CryptographicOperations.FixedTimeEquals(actual, expectedHash);
        }
        finally
        {
            CryptographicOperations.ZeroMemory(pinBytes);
        }
    }
}

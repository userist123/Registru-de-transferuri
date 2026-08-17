using System.Runtime.InteropServices;
using System.Security.Cryptography;

namespace RegistruTransferuri.Security;

/// <summary>
/// Buffer de memorie securizat conform standardelor militare:
/// - Alocare fixata in RAM (pinned) pentru a preveni duplicarea necontrolata de catre Garbage Collector in timpul compactarii
/// - Epurare garantata la Dispose prin CryptographicOperations.ZeroMemory() (imuna la Dead Code Elimination)
/// </summary>
public sealed class SecureBuffer : IDisposable
{
    private byte[]? _buffer;
    private GCHandle _handle;
    private bool _disposed;

    public int Length => _buffer?.Length ?? 0;
    public Span<byte> Span => _buffer != null ? _buffer.AsSpan() : Span<byte>.Empty;
    public ReadOnlySpan<byte> ReadOnlySpan => _buffer != null ? new ReadOnlySpan<byte>(_buffer) : ReadOnlySpan<byte>.Empty;

    public SecureBuffer(int size)
    {
        if (size <= 0) throw new ArgumentOutOfRangeException(nameof(size));
        _buffer = GC.AllocateArray<byte>(size, pinned: true);
        _handle = GCHandle.Alloc(_buffer, GCHandleType.Pinned);
    }

    public SecureBuffer(ReadOnlySpan<byte> source) : this(source.Length)
    {
        source.CopyTo(_buffer);
    }

    public static SecureBuffer FromString(string text)
    {
        var bytes = System.Text.Encoding.UTF8.GetBytes(text);
        var buf = new SecureBuffer(bytes);
        CryptographicOperations.ZeroMemory(bytes);
        return buf;
    }

    public void Wipe()
    {
        if (_buffer != null)
        {
            CryptographicOperations.ZeroMemory(_buffer);
        }
    }

    public void Dispose()
    {
        if (!_disposed)
        {
            Wipe();
            if (_handle.IsAllocated)
            {
                _handle.Free();
            }
            _buffer = null;
            _disposed = true;
            GC.SuppressFinalize(this);
        }
    }

    ~SecureBuffer()
    {
        Dispose();
    }
}

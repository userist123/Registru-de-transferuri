using System.IO;
using System.Security.Cryptography;

namespace RegistruTransferuri.Security;

/// <summary>
/// Protectia cheii master SQLCipher prin Windows DPAPI (Data Protection API).
/// Scope LocalMachine: cheia poate fi decifrata DOAR pe aceasta statie fizica.
/// Daca SSD-ul este sustras si montat pe alt sistem, cheia ramane indescifrabila.
/// </summary>
public static class DpapiKeyProtector
{
    private static readonly byte[] Entropy = "RegistruTransferuri.v3.1.MAPN"u8.ToArray();

    public static byte[] GenerateAndProtect(string protectedKeyPath)
    {
        var key = RandomNumberGenerator.GetBytes(32);
        try
        {
            var protectedKey = ProtectedData.Protect(key, Entropy, DataProtectionScope.LocalMachine);
            File.WriteAllBytes(protectedKeyPath, protectedKey);
            var fi = new FileInfo(protectedKeyPath);
            fi.Attributes |= FileAttributes.Hidden;
            return key;
        }
        catch
        {
            CryptographicOperations.ZeroMemory(key);
            throw;
        }
    }

    public static SecureBuffer UnprotectToSecureBuffer(string protectedKeyPath)
    {
        var protectedKey = File.ReadAllBytes(protectedKeyPath);
        var rawKey = ProtectedData.Unprotect(protectedKey, Entropy, DataProtectionScope.LocalMachine);
        var buffer = new SecureBuffer(rawKey.Length);
        rawKey.CopyTo(buffer.Span);
        CryptographicOperations.ZeroMemory(rawKey);
        return buffer;
    }
}

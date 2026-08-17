using System.Security.Cryptography;
using System.Text;
using Konscious.Security.Cryptography;

namespace RegistruTransferuri.Security;

/// <summary>
/// Derivare securizata a codurilor PIN utilizand Argon2id (m=64MB, t=3, p=4, salt=16B)
/// Imuna la atacuri offline GPU/ASIC conform standardelor moderne INFOSEC.
/// </summary>
public static class PinHasher
{
    public static (byte[] Hash, byte[] Salt) HashPin(string pin)
    {
        var salt = RandomNumberGenerator.GetBytes(16);
        using var argon2 = new Argon2id(Encoding.UTF8.GetBytes(pin))
        {
            Salt = salt,
            DegreeOfParallelism = 4,
            Iterations = 3,
            MemorySize = 65536 // 64 MB RAM
        };
        var hash = argon2.GetBytes(32);
        return (hash, salt);
    }

    public static bool VerifyPin(string pin, byte[] storedHash, byte[] storedSalt)
    {
        try
        {
            using var argon2 = new Argon2id(Encoding.UTF8.GetBytes(pin))
            {
                Salt = storedSalt,
                DegreeOfParallelism = 4,
                Iterations = 3,
                MemorySize = 65536
            };
            var testHash = argon2.GetBytes(32);
            return CryptographicOperations.FixedTimeEquals(testHash, storedHash);
        }
        catch
        {
            return false;
        }
    }
}

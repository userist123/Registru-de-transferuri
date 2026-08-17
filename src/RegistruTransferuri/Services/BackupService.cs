using System.IO;
using System.Security.Cryptography;

namespace RegistruTransferuri.Services;

/// <summary>
/// Backup automat al bazei SQLCipher cu rotatie (ultimele 30 de versiuni).
/// Fisierul de backup ramane criptat — copierea nu degradeaza protectia AES-256.
/// Fiecare backup primeste un manifest SHA-256 pentru verificarea integritatii la restaurare.
/// </summary>
public sealed class BackupService
{
    private const int MaxBackups = 30;

    public string CreateBackup(string dbPath, string backupDir)
    {
        Directory.CreateDirectory(backupDir);
        var stamp = DateTime.UtcNow.ToString("yyyyMMdd-HHmmss");
        var backupPath = Path.Combine(backupDir, $"transferuri-{stamp}.db.bak");
        File.Copy(dbPath, backupPath, overwrite: false);

        var hash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(backupPath)));
        File.WriteAllText(backupPath + ".sha256", hash);

        RotateBackups(backupDir);
        return backupPath;
    }

    public bool VerifyBackup(string backupPath)
    {
        var manifestPath = backupPath + ".sha256";
        if (!File.Exists(manifestPath)) return false;
        var expected = File.ReadAllText(manifestPath).Trim();
        var actual = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(backupPath)));
        return string.Equals(expected, actual, StringComparison.OrdinalIgnoreCase);
    }

    private static void RotateBackups(string backupDir)
    {
        var backups = Directory.GetFiles(backupDir, "transferuri-*.db.bak")
            .OrderByDescending(f => f).Skip(MaxBackups).ToList();
        foreach (var old in backups)
        {
            File.Delete(old);
            var manifest = old + ".sha256";
            if (File.Exists(manifest)) File.Delete(manifest);
        }
    }
}

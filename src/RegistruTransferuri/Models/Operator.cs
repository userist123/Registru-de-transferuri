namespace RegistruTransferuri.Models;

/// <summary>Operator cu clearance — autentificare Smart Card PKCS#11 sau PIN salted.</summary>
public sealed class Operator
{
    public long Id { get; set; }
    public string Username { get; set; } = "";
    public string FullName { get; set; } = "";
    public string Role { get; set; } = "Operator";
    public ClassificationLevel MaxClearance { get; set; } = ClassificationLevel.Neclasificat;
    public byte[] PinSalt { get; set; } = Array.Empty<byte>();
    public byte[] PinHash { get; set; } = Array.Empty<byte>();
    public string? SmartCardSubjectDn { get; set; }
    public bool Active { get; set; } = true;

    public bool CanAccess(ClassificationLevel level) => level <= MaxClearance;
}

namespace RegistruTransferuri.Models;

public sealed class Operator
{
    public int Id { get; set; }
    public string Username { get; set; } = string.Empty;
    public string FullName { get; set; } = string.Empty;
    public string Role { get; set; } = "Operator";
    public string MilitaryUnit { get; set; } = "MApN / Structura Securitate";
    public ClassificationLevel MaxClearance { get; set; } = ClassificationLevel.Secret;
    public string NatoClearance => MaxClearance.ToNatoClassification();
    public byte[] PinSalt { get; set; } = Array.Empty<byte>();
    public byte[] PinHash { get; set; } = Array.Empty<byte>();
    public string? SmartcardDn { get; set; }
    public bool Active { get; set; } = true;
    public DateTime? LastLoginUtc { get; set; }

    public bool CanAccess(ClassificationLevel level) => (int)level <= (int)MaxClearance;
}

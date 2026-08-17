using System;
using System.Collections.Generic;
using System.Linq;
using RegistruTransferuri.Models;
using RegistruTransferuri.Security;
using Xunit;

namespace RegistruTransferuri.Tests;

public class SecurityTests
{
    [Fact]
    public void RegistryPrefix_ConformArt41_HG585()
    {
        Assert.Equal("000", ClassificationLevel.StrictSecretImportantaDeosebita.RegistryPrefix());
        Assert.Equal("00", ClassificationLevel.StrictSecret.RegistryPrefix());
        Assert.Equal("0", ClassificationLevel.Secret.RegistryPrefix());
        Assert.Equal("S", ClassificationLevel.SecretDeServiciu.RegistryPrefix());
        Assert.Equal("NC", ClassificationLevel.Neclasificat.RegistryPrefix());
    }

    [Fact]
    public void IntegrityHash_DetecteazaOriceModificare()
    {
        var t = new TransferRecord
        {
            RegistryNumber = "MAPN-2026-000-0001",
            Classification = ClassificationLevel.StrictSecretImportantaDeosebita,
            TransferDateUtc = DateTime.UtcNow,
            SourceInstitution = "MAPN", DestinationInstitution = "SRI",
            SourcePerson = "A", DestinationPerson = "B",
            MediaType = "USB", MediaSerialNumber = "SN123",
            OperatorUsername = "op1"
        };
        t.IntegrityHash = t.ComputeIntegrityHash();
        Assert.True(t.VerifyIntegrity());

        t.DestinationInstitution = "MODIFICAT";
        Assert.False(t.VerifyIntegrity());
    }

    [Fact]
    public void AuditChain_DetecteazaStergereSiModificare()
    {
        var entries = new List<AuditEntry>();
        var prev = AuditChain.GenesisHash;
        for (long i = 1; i <= 5; i++)
        {
            var ts = DateTime.UtcNow;
            var h = AuditChain.ComputeEntryHash(prev, i, ts, "ACT", "op", $"d{i}");
            entries.Add(new AuditEntry(i, ts, "ACT", "op", $"d{i}", prev, h));
            prev = h;
        }
        Assert.Equal(-1, AuditChain.VerifyChain(entries));

        var tampered = entries.ToList();
        tampered[2] = tampered[2] with { Details = "FALSIFICAT" };
        Assert.Equal(3, AuditChain.VerifyChain(tampered));

        var deleted = entries.Where(e => e.Sequence != 3).ToList();
        Assert.True(AuditChain.VerifyChain(deleted) > 0);
    }

    [Fact]
    public void MerkleTree_ProbaDePrezenta()
    {
        var leaves = Enumerable.Range(0, 100)
            .Select(i => Convert.ToHexString(
                System.Security.Cryptography.SHA256.HashData(
                    System.Text.Encoding.UTF8.GetBytes($"entry-{i}"))))
            .ToList();
        var root = MerkleTree.ComputeRoot(leaves);
        var proof = MerkleTree.GenerateProof(leaves, 42);
        Assert.True(MerkleTree.VerifyProof(leaves[42], proof, root));
        Assert.False(MerkleTree.VerifyProof(leaves[43], proof, root));
    }

    [Fact]
    public void PinHasher_VerificareInTimpConstant()
    {
        var (hash, salt) = PinHasher.HashPin("123456");
        Assert.True(PinHasher.VerifyPin("123456", hash, salt));
        Assert.False(PinHasher.VerifyPin("654321", hash, salt));
    }

    [Fact]
    public void Sanitization_MinimumConformNist80088r2()
    {
        Assert.Equal(SanitizationMethod.Clear, ClassificationLevel.Neclasificat.MinimumSanitization());
        Assert.Equal(SanitizationMethod.Purge, ClassificationLevel.SecretDeServiciu.MinimumSanitization());
        Assert.Equal(SanitizationMethod.Destroy, ClassificationLevel.Secret.MinimumSanitization());
        Assert.Equal(SanitizationMethod.Destroy, ClassificationLevel.StrictSecretImportantaDeosebita.MinimumSanitization());
    }
}

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using RegistruTransferuri.Data;
using RegistruTransferuri.Models;
using RegistruTransferuri.Security;
using RegistruTransferuri.Services;
using Xunit;

namespace RegistruTransferuri.Tests;

public class SecurityTests
{
    [Fact]
    public void RegistryPrefix_ConformArt41_HG585()
    {
        Assert.Equal("000", ClassificationLevel.StrictSecretDeImportantaDeosebita.GetPrefix());
        Assert.Equal("00", ClassificationLevel.StrictSecret.GetPrefix());
        Assert.Equal("0", ClassificationLevel.Secret.GetPrefix());
        Assert.Equal("S", ClassificationLevel.SecretDeServiciu.GetPrefix());
        Assert.Equal("NC", ClassificationLevel.Neclasificat.GetPrefix());
    }

    [Fact]
    public void NatoEquivalent_ConformNATO_AC35()
    {
        Assert.Equal("COSMIC TOP SECRET", ClassificationLevel.StrictSecretDeImportantaDeosebita.ToNatoClassification());
        Assert.Equal("NATO SECRET", ClassificationLevel.StrictSecret.ToNatoClassification());
        Assert.Equal("NATO CONFIDENTIAL", ClassificationLevel.Secret.ToNatoClassification());
        Assert.Equal("NATO RESTRICTED", ClassificationLevel.SecretDeServiciu.ToNatoClassification());
        Assert.Equal("NATO UNCLASSIFIED", ClassificationLevel.Neclasificat.ToNatoClassification());
    }

    [Fact]
    public void EuEquivalent_ConformEUCI()
    {
        Assert.Equal("TRÈS SECRET UE / EU TOP SECRET", ClassificationLevel.StrictSecretDeImportantaDeosebita.ToEuClassification());
        Assert.Equal("SECRET UE / EU SECRET", ClassificationLevel.StrictSecret.ToEuClassification());
        Assert.Equal("CONFIDENTIEL UE / EU CONFIDENTIAL", ClassificationLevel.Secret.ToEuClassification());
        Assert.Equal("RESTREINT UE / EU RESTRICTED", ClassificationLevel.SecretDeServiciu.ToEuClassification());
    }

    [Fact]
    public void MerkleTree_ProbaDePrezenta()
    {
        var leaves = Enumerable.Range(0, 100)
            .Select(i => Convert.ToHexString(
                SHA256.HashData(
                    Encoding.UTF8.GetBytes($"entry-{i}"))))
            .ToList();
        var root = MerkleTree.ComputeRoot(leaves);
        var proof = MerkleTree.GenerateProof(leaves, 42);
        Assert.True(MerkleTree.VerifyProof(leaves[42], proof, root));
        Assert.False(MerkleTree.VerifyProof(leaves[43], proof, root));
    }

    [Fact]
    public void CognitiveBridge_OracleAndSynthesis()
    {
        var bridge = new CognitiveVaultBridgeService();
        var answer = bridge.AskSecurityOracle("sanitizare nist");
        Assert.Contains("NIST SP 800-88", answer);

        var tx = new TransferRecord
        {
            RegistryNumber = "MAPN-2026-S-0001",
            Classification = ClassificationLevel.Secret,
            TransferDateUtc = DateTime.UtcNow,
            SourceInstitution = "MApN",
            DestinationInstitution = "Statul Major",
            SourcePerson = "Cpt. Ionescu",
            MediaType = "Stick USB",
            MediaSerialNumber = "TEST-SN-12345",
            MediaVendorId = "0781",
            MediaProductId = "5567",
            PayloadFileName = "test_doc.zip",
            PayloadSha256Hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            OperatorUsername = "Admin"
        };
        var (success, _) = bridge.SynthesizeTransferToVault(tx);
        Assert.True(success);
    }

    [Fact]
    public void DatabaseContext_FullTransferAndAuditLifecycle()
    {
        var tempDb = Path.Combine(Path.GetTempPath(), $"test_db_{Guid.NewGuid():N}.sqlite3");
        try
        {
            using var db = new DatabaseContext(tempDb);

            // 1. Operatori default
            var ops = db.GetActiveOperators();
            Assert.True(ops.Count >= 2);

            // 2. Autentificare PIN
            var auth = db.Authenticate(ops[0].Id, "123456");
            Assert.NotNull(auth);

            // 3. Adaugare Transfer
            var tx = new TransferRecord
            {
                RegistryNumber = "2150-23SSv",
                Classification = ClassificationLevel.SecretDeServiciu,
                TransferDateUtc = DateTime.UtcNow,
                SourceInstitution = "MApN",
                DestinationInstitution = "Baza 1",
                SourcePerson = "Cpt. Popescu",
                MediaType = "Stick USB",
                MediaSerialNumber = "HW-SN-9999",
                MediaFriendlyLabel = "Stick Operativ 01",
                PayloadFileName = "2150-23SSv.zip",
                PayloadSha256Hash = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
                OperatorUsername = auth.FullName
            };
            db.InsertTransfer(tx);

            var retrieved = db.GetTransfers("2150-23SSv");
            Assert.Single(retrieved);
            Assert.Equal("2150-23SSv", retrieved[0].RegistryNumber);

            // 4. Verificare Lant Audit
            var (valid, count, error) = db.VerifyAuditChain();
            Assert.True(valid);
            Assert.True(count >= 2);
            Assert.Null(error);
        }
        finally
        {
            if (File.Exists(tempDb))
            {
                try { File.Delete(tempDb); } catch { }
            }
        }
    }

    [Fact]
    public void MediaEnrollment_And_FriendlyNameUpdate()
    {
        var tempDb = Path.Combine(Path.GetTempPath(), $"test_media_{Guid.NewGuid():N}.sqlite3");
        try
        {
            using var db = new DatabaseContext(tempDb);

            var asset = new MediaAsset
            {
                SerialNumber = "KINGSTON-00123",
                InventoryCode = "0-1045/2026",
                FriendlyName = "Stick Transfer Operativ MApN 01",
                MediaType = "Stick USB Flash",
                VendorId = "0951",
                ProductId = "1666",
                CapacityBytes = 32_000_000_000L,
                MaxClassification = ClassificationLevel.Secret,
                Status = MediaStatus.AutorizatRw,
                CustodianName = "Cpt. Radu"
            };

            db.AddOrUpdateMedia(asset, "Admin");

            var list = db.GetMediaAssets("KINGSTON");
            Assert.Single(list);
            Assert.Equal("Stick Transfer Operativ MApN 01", list[0].FriendlyName);

            // Update Friendly Name
            db.UpdateMediaFriendlyName(list[0].Id, "Stick Operativ Redenumit [0-1045/2026]", "Admin");
            var updated = db.GetMediaAssets("Redenumit");
            Assert.Single(updated);
            Assert.Equal("Stick Operativ Redenumit [0-1045/2026]", updated[0].FriendlyName);
        }
        finally
        {
            if (File.Exists(tempDb))
            {
                try { File.Delete(tempDb); } catch { }
            }
        }
    }

    [Fact]
    public void ExportService_GeneratesValidHtml()
    {
        var exporter = new PadesExportService();
        var tx = new TransferRecord
        {
            RegistryNumber = "MAPN-2026-S-0001",
            Classification = ClassificationLevel.Secret,
            TransferDateUtc = DateTime.UtcNow,
            SourceInstitution = "MApN / Structura Securitate",
            SourceStationHost = "PC-SECURE-01",
            SourcePerson = "Cpt. Ionescu Radu",
            DestinationInstitution = "Statul Major",
            DestinationPerson = "Mr. Popa",
            MediaType = "Stick USB",
            MediaSerialNumber = "SN-987654",
            PayloadFileName = "Date_Operative.zip",
            PayloadSha256Hash = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            OperatorUsername = "Operator 1"
        };

        var html = exporter.GenerateProcesVerbalHtml(tx);
        Assert.Contains("PROCES-VERBAL DE PREDARE-PRIMIRE", html);
        Assert.Contains("HG 585/2002 Art. 65-72", html);
        Assert.Contains("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", html);
    }
}

using System.Security.Cryptography;

namespace RegistruTransferuri.Security;

/// <summary>
/// Arbore Merkle peste intrarile de audit zilnice — verificare logaritmica O(log n).
/// Permite emiterea unei Merkle Proof pentru o singura inregistrare fara recalcularea
/// intregului istoric (conform art. 73 HG 585/2002 — verificarea anuala).
/// </summary>
public static class MerkleTree
{
    public static string ComputeRoot(IReadOnlyList<string> leafHashes)
    {
        if (leafHashes.Count == 0) return AuditChain.GenesisHash;
        var level = leafHashes.Select(HexToBytes).ToList();
        while (level.Count > 1)
        {
            var next = new List<byte[]>();
            for (int i = 0; i < level.Count; i += 2)
            {
                var left = level[i];
                var right = i + 1 < level.Count ? level[i + 1] : level[i];
                next.Add(SHA256.HashData(Concat(left, right)));
            }
            level = next;
        }
        return Convert.ToHexString(level[0]);
    }

    public static List<(byte[] Sibling, bool IsLeft)> GenerateProof(IReadOnlyList<string> leafHashes, int index)
    {
        var proof = new List<(byte[], bool)>();
        var level = leafHashes.Select(HexToBytes).ToList();
        int idx = index;
        while (level.Count > 1)
        {
            int siblingIdx = idx % 2 == 0 ? idx + 1 : idx - 1;
            if (siblingIdx < level.Count)
                proof.Add((level[siblingIdx], idx % 2 != 0));
            else
                proof.Add((level[idx], idx % 2 != 0));
            var next = new List<byte[]>();
            for (int i = 0; i < level.Count; i += 2)
            {
                var right = i + 1 < level.Count ? level[i + 1] : level[i];
                next.Add(SHA256.HashData(Concat(level[i], right)));
            }
            level = next;
            idx /= 2;
        }
        return proof;
    }

    public static bool VerifyProof(string leafHash, List<(byte[] Sibling, bool IsLeft)> proof, string expectedRoot)
    {
        var current = HexToBytes(leafHash);
        foreach (var (sibling, isLeft) in proof)
            current = isLeft ? SHA256.HashData(Concat(sibling, current))
                             : SHA256.HashData(Concat(current, sibling));
        return Convert.ToHexString(current) == expectedRoot;
    }

    private static byte[] HexToBytes(string hex) => Convert.FromHexString(hex);
    private static byte[] Concat(byte[] a, byte[] b)
    {
        var r = new byte[a.Length + b.Length];
        Buffer.BlockCopy(a, 0, r, 0, a.Length);
        Buffer.BlockCopy(b, 0, r, a.Length, b.Length);
        return r;
    }
}

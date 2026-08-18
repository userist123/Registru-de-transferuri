using System.IO;
using System.Text.RegularExpressions;
using RegistruTransferuri.Models;

namespace RegistruTransferuri.Services;

public sealed record ParsedFileNameInfo(
    string? ExtractedRegistryNumber,
    ClassificationLevel? SuggestedClassification,
    string CleanFileName,
    bool Success
);

/// <summary>
/// Parser euristic militar pentru extragerea automată a numărului de înregistrare și clasificării din denumirea fișierelor.
/// Suportă tiparele HG 585 (prefixe 000/00/0/S/NC, tipare MApN, NATO).
/// </summary>
public static class FileNameRegistryParser
{
    // Tipar 1: MAPN-2026-S-0042 sau MAPN-2026-0-0042
    private static readonly Regex MapnFullRegex = new(
        @"(?<prefix>MAPN|MApN|UM\d{4,5})[-_ ](?<an>20\d{2})[-_ ](?<clasif>SSID|SSv|SS|STRICT_SECRET|SECRET|CONFIDENTIAL|RESTRICTED|NC|S|000|00|0)[-_ ](?<nr>\d{1,6})",
        RegexOptions.IgnoreCase | RegexOptions.Compiled
    );

    // Tipar 2: Prefixe HG 585 canonice (000-55-2026 sau 00-1045-26)
    private static readonly Regex Hg585PrefixRegex = new(
        @"^(?<pfx>000|00|0|S|NC)[-_ ](?<nr>\d{1,6})[-_ ](?<an>20\d{2}|\d{2})",
        RegexOptions.IgnoreCase | RegexOptions.Compiled
    );

    // Tipar 3: Simplu (ex: 1045-26SS sau 1045-2026-S)
    private static readonly Regex SimpleRegRegex = new(
        @"^(?<nr>\d{1,6})[-_](?<an>20\d{2}|\d{2})[-_]?(?<clasif>SSID|SSv|SS|S|NC)?",
        RegexOptions.IgnoreCase | RegexOptions.Compiled
    );

    public static ParsedFileNameInfo Parse(string filePath)
    {
        var fileName = Path.GetFileNameWithoutExtension(filePath);
        if (string.IsNullOrWhiteSpace(fileName))
            return new ParsedFileNameInfo(null, null, "", false);

        // 1. Tipar MAPN complet
        var matchFull = MapnFullRegex.Match(fileName);
        if (matchFull.Success)
        {
            var an = matchFull.Groups["an"].Value;
            var nr = matchFull.Groups["nr"].Value.PadLeft(4, '0');
            var clasifStr = matchFull.Groups["clasif"].Value.ToUpperInvariant();
            var clf = ResolveClassification("", clasifStr);
            var regNr = $"MAPN-{an}-{clf.GetPrefix()}-{nr}";
            return new ParsedFileNameInfo(regNr, clf, fileName, true);
        }

        // 2. Tipar HG 585 cu prefix (000-55-2026)
        var matchHg = Hg585PrefixRegex.Match(fileName);
        if (matchHg.Success)
        {
            var pfx = matchHg.Groups["pfx"].Value.ToUpperInvariant();
            var nr = matchHg.Groups["nr"].Value.PadLeft(4, '0');
            var an = matchHg.Groups["an"].Value;
            if (an.Length == 2) an = "20" + an;
            var clf = ResolveClassification(pfx, "");
            var regNr = $"MAPN-{an}-{clf.GetPrefix()}-{nr}";
            return new ParsedFileNameInfo(regNr, clf, fileName, true);
        }

        // 3. Tipar simplu (1045-26SS)
        var simpleMatch = SimpleRegRegex.Match(fileName);
        if (simpleMatch.Success)
        {
            var nr = simpleMatch.Groups["nr"].Value.PadLeft(4, '0');
            var an = simpleMatch.Groups["an"].Value;
            if (an.Length == 2) an = "20" + an;
            var clasifStr = simpleMatch.Groups["clasif"].Value.ToUpperInvariant();
            var clf = ResolveClassification("", clasifStr);
            var regNr = $"MAPN-{an}-{clf.GetPrefix()}-{nr}";
            return new ParsedFileNameInfo(regNr, clf, fileName, true);
        }

        return new ParsedFileNameInfo(null, null, fileName, false);
    }

    private static ClassificationLevel ResolveClassification(string prefix, string clasifStr)
    {
        if (prefix == "000" || clasifStr == "SSID" || clasifStr == "000")
            return ClassificationLevel.StrictSecretDeImportantaDeosebita;
        if (prefix == "00" || clasifStr == "SS" || clasifStr == "00" || clasifStr.Contains("STRICT"))
            return ClassificationLevel.StrictSecret;
        if (prefix == "0" || clasifStr == "S" || clasifStr == "0" || clasifStr.Contains("SECRET"))
            return ClassificationLevel.Secret;
        if (prefix == "S" || clasifStr == "SSV" || clasifStr.Contains("SERVICIU") || clasifStr.Contains("RESTRICTED"))
            return ClassificationLevel.SecretDeServiciu;
        if (prefix == "NC" || clasifStr == "NC" || clasifStr.Contains("NECLASIF") || clasifStr.Contains("UNCLASSIFIED"))
            return ClassificationLevel.Neclasificat;

        return ClassificationLevel.Secret;
    }
}

using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using NLog;
using NzbDrone.Common.EnvironmentInfo;
using NzbDrone.Common.Http;

namespace NzbDrone.Core.Update
{
    public interface IUpdateAttestationVerifier
    {
        bool Verify(UpdatePackage package, string path);
    }

    public class UpdateAttestationVerifier : IUpdateAttestationVerifier
    {
        internal const string PredicateType = "https://github.com/snapetech-org/chaptarrng/release/v1";
        private readonly IHttpClient _http;
        private readonly IAppFolderInfo _folders;
        private readonly Logger _logger;

        public UpdateAttestationVerifier(IHttpClient http, IAppFolderInfo folders, Logger logger)
        {
            _http = http;
            _folders = folders;
            _logger = logger;
        }

        public bool Verify(UpdatePackage package, string path)
        {
            if (!IsTrustedPackage(package))
            {
                return false;
            }

            var source = new Uri(package.Url);

            var executable = FindVerifier();
            if (executable == null)
            {
                _logger.Error("Update signature verification requires the GitHub CLI (gh) with attestation support. Install it before updating.");
                return false;
            }

            var temporary = Path.Combine(_folders.TempFolder, "update-attestation-" + Guid.NewGuid().ToString("N"));
            try
            {
                if (OperatingSystem.IsWindows()) { Directory.CreateDirectory(temporary); }
                else { Directory.CreateDirectory(temporary, UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.UserExecute); }
                var response = _http.Get(new HttpRequest(source.GetLeftPart(UriPartial.Path) + ".sigstore.json")
                {
                    MaxResponseBytes = 4 * 1024 * 1024, AllowPrivateNetworkTargets = false,
                    RequestTimeout = TimeSpan.FromSeconds(30), StoreRequestCookie = false, StoreResponseCookie = false
                });
                var bundle = Path.Combine(temporary, "bundle.json");
                File.WriteAllBytes(bundle, response.ResponseData);
                var start = new ProcessStartInfo(executable)
                {
                    UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true
                };
                foreach (var argument in new[]
                {
                    "attestation", "verify", Path.GetFullPath(path), "--bundle", bundle,
                    "--repo", "snapetech-org/chaptarrng",
                    "--cert-identity", "https://github.com/snapetech-org/chaptarrng/.github/workflows/release.yml@refs/heads/main",
                    "--source-ref", "refs/heads/main", "--deny-self-hosted-runners",
                    "--predicate-type", PredicateType, "--format", "json"
                }) { start.ArgumentList.Add(argument); }
                start.Environment["GH_PROMPT_DISABLED"] = "1";
                start.Environment["GH_HOST"] = "github.com";
                start.Environment["GH_CONFIG_DIR"] = temporary;
                start.Environment.Remove("GH_TOKEN");
                start.Environment.Remove("GITHUB_TOKEN");
                using var process = Process.Start(start);
                if (process == null) { return false; }
                var output = ReadBounded(process.StandardOutput, process, 1024 * 1024);
                var errors = ReadBounded(process.StandardError, process, 64 * 1024);
                if (!process.WaitForExit(60000))
                {
                    process.Kill(true);
                    return false;
                }

                if (!Task.WaitAll(new Task[] { output, errors }, 5000) || process.ExitCode != 0) { return false; }
                return MatchesRelease(output.GetAwaiter().GetResult(), package);
            }
            catch (Exception exception)
            {
                _logger.Warn(exception, "Update attestation verification failed; refusing installation.");
                return false;
            }
            finally
            {
                try { if (Directory.Exists(temporary)) { Directory.Delete(temporary, true); } }
                catch (IOException) { }
                catch (UnauthorizedAccessException) { }
            }
        }

        internal static bool IsTrustedPackage(UpdatePackage package) => package?.Version != null &&
            Uri.TryCreate(package.Url, UriKind.Absolute, out var source) && source.Scheme == Uri.UriSchemeHttps &&
            source.Host == "github.com" && source.Port == 443 &&
            source.AbsolutePath.StartsWith("/snapetech-org/chaptarrng/releases/download/", StringComparison.Ordinal) &&
            string.IsNullOrEmpty(source.Query) && string.IsNullOrEmpty(source.Fragment) && string.IsNullOrEmpty(source.UserInfo);

        internal static bool MatchesRelease(string verifiedJson, UpdatePackage package)
        {
            if (package?.Hash?.Length != 64 || !package.Hash.All(Uri.IsHexDigit)) { return false; }
            using var document = JsonDocument.Parse(verifiedJson);
            if (document.RootElement.ValueKind != JsonValueKind.Array) { return false; }
            foreach (var verification in document.RootElement.EnumerateArray())
            {
                if (!verification.TryGetProperty("verificationResult", out var result) ||
                    !result.TryGetProperty("statement", out var statement) ||
                    !statement.TryGetProperty("predicateType", out var type) || type.GetString() != PredicateType ||
                    !statement.TryGetProperty("predicate", out var predicate) ||
                    !predicate.TryGetProperty("version", out var versionElement) ||
                    !Version.TryParse(versionElement.GetString()?.TrimStart('v'), out var version) ||
                    version.Major != package.Version.Major || version.Minor != package.Version.Minor ||
                    version.Build != package.Version.Build || Math.Max(0, version.Revision) != Math.Max(0, package.Version.Revision) ||
                    !statement.TryGetProperty("subject", out var subjects)) { continue; }
                if (subjects.EnumerateArray().Any(subject => subject.TryGetProperty("name", out var name) &&
                    Path.GetFileName(name.GetString()) == package.FileName &&
                    subject.TryGetProperty("digest", out var digest) &&
                    digest.TryGetProperty("sha256", out var hash) &&
                    string.Equals(hash.GetString(), package.Hash, StringComparison.OrdinalIgnoreCase))) { return true; }
            }

            return false;
        }

        private string FindVerifier()
        {
            var candidates = new[]
            {
                Path.Combine(_folders.StartUpFolder, "Tools", OperatingSystem.IsWindows() ? "gh.exe" : "gh"),
                "/usr/bin/gh", "/usr/local/bin/gh", "/opt/homebrew/bin/gh",
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "GitHub CLI", "gh.exe")
            };
            return candidates.FirstOrDefault(File.Exists);
        }

        private static async Task<string> ReadBounded(StreamReader reader, Process process, int limit)
        {
            var result = new StringBuilder();
            var buffer = new char[4096];
            int count;
            while ((count = await reader.ReadAsync(buffer, 0, buffer.Length)) > 0)
            {
                if (count > limit - result.Length)
                {
                    try { process.Kill(true); } catch (InvalidOperationException) { }
                    throw new InvalidDataException("Attestation verifier output exceeded its limit.");
                }

                result.Append(buffer, 0, count);
            }

            return result.ToString();
        }
    }
}

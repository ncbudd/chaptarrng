using System;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Security.Cryptography;
using Moq;
using NLog;
using NUnit.Framework;
using NzbDrone.Common.Disk;
using NzbDrone.Common.EnvironmentInfo;
using NzbDrone.Common.Http;
using NzbDrone.Core.Update;

namespace Chaptarr.Core.Test.Update
{
    [TestFixture]
    public class UpdateAttestationFixture
    {
        [TestCase("v1.2.3", "app.tar.gz", true)]
        [TestCase("1.2.3.0", "app.tar.gz", true)]
        [TestCase("1.2.2", "app.tar.gz", false)]
        [TestCase("1.2.3.1", "app.tar.gz", false)]
        [TestCase("1.2.3", "other.tar.gz", false)]
        public void verified_statement_must_bind_both_version_and_archive(string version, string name, bool expected)
        {
            var hash = new string('a', 64);
            var json = JsonSerializer.Serialize(new[] { new
            {
                verificationResult = new { statement = new
                {
                    predicateType = UpdateAttestationVerifier.PredicateType,
                    predicate = new { version }, subject = new[] { new { name, digest = new { sha256 = hash } } }
                } }
            } });
            Assert.That(UpdateAttestationVerifier.MatchesRelease(json, new UpdatePackage
            {
                Version = new Version(1, 2, 3), FileName = "app.tar.gz", Hash = hash
            }), Is.EqualTo(expected));
        }

        [TestCase(false)]
        [TestCase(true)]
        public void archive_name_and_digest_must_match_the_same_attested_subject(bool correctDigest)
        {
            var hash = new string('a', 64);
            var otherHash = new string('b', 64);
            var json = JsonSerializer.Serialize(new[] { new
            {
                verificationResult = new { statement = new
                {
                    predicateType = UpdateAttestationVerifier.PredicateType,
                    predicate = new { version = "1.2.3" },
                    subject = new[]
                    {
                        new { name = "app.tar.gz", digest = new { sha256 = correctDigest ? hash.ToUpperInvariant() : otherHash } },
                        new { name = "other.tar.gz", digest = new { sha256 = hash } }
                    }
                } }
            } });
            Assert.That(UpdateAttestationVerifier.MatchesRelease(json, new UpdatePackage
            {
                Version = new Version(1, 2, 3), FileName = "app.tar.gz", Hash = hash
            }), Is.EqualTo(correctDigest));
        }

        [TestCase(false)]
        [TestCase(true)]
        public void matching_download_checksum_is_insufficient_without_valid_attestation(bool trusted)
        {
            var bytes = Encoding.UTF8.GetBytes("archive fixture");
            var disk = new Mock<IDiskProvider>();
            disk.Setup(d => d.OpenReadStream("archive")).Returns(() => new MemoryStream(bytes));
            var package = new UpdatePackage { Hash = Convert.ToHexString(SHA256.HashData(bytes)) };
            var attestation = new Mock<IUpdateAttestationVerifier>();
            attestation.Setup(a => a.Verify(package, "archive")).Returns(trusted);
            Assert.That(new UpdateVerification(disk.Object, attestation.Object).Verify(package, "archive"), Is.EqualTo(trusted));
            attestation.Verify(a => a.Verify(package, "archive"), Times.Once);
        }

        [TestCase("https://github.com/another/project/releases/download/v1/app.tar.gz")]
        [TestCase("http://github.com/snapetech-org/chaptarrng/releases/download/v1/app.tar.gz")]
        [TestCase("https://github.com:444/snapetech-org/chaptarrng/releases/download/v1/app.tar.gz")]
        [TestCase("https://owner@github.com/snapetech-org/chaptarrng/releases/download/v1/app.tar.gz")]
        public void refuses_untrusted_release_origins_before_network_or_process_execution(string url)
        {
            var http = new Mock<IHttpClient>(MockBehavior.Strict);
            var verifier = new UpdateAttestationVerifier(http.Object, new Mock<IAppFolderInfo>(MockBehavior.Strict).Object, LogManager.GetCurrentClassLogger());
            Assert.That(verifier.Verify(new UpdatePackage { Version = new Version(1, 2, 3), Url = url }, "archive"), Is.False);
            http.VerifyNoOtherCalls();
        }
    }
}

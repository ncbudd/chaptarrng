using System;
using System.IO;
using Moq;
using NUnit.Framework;
using NzbDrone.Common.EnvironmentInfo;
using NzbDrone.Common.Disk;
using Microsoft.Data.Sqlite;
using NzbDrone.Common.Extensions;
using NzbDrone.Core.Datastore;

namespace Chaptarr.Core.Test.Datastore
{
    [TestFixture]
    public class FullRestoreBundleFixture
    {
        [Test]
        public void source_only_ssl_certificate_rejects_restore_before_staging()
        {
            var root = Path.Combine(Path.GetTempPath(), "chaptarr-restore-ssl-" + Guid.NewGuid());
            Directory.CreateDirectory(root);
            var folders = new Mock<IAppFolderInfo>();
            folders.SetupGet(f => f.AppDataFolder).Returns(root);
            var info = folders.Object;
            try
            {
                File.WriteAllText(info.GetDatabase(), "original database");
                File.WriteAllText(info.GetConfigPath(), "<Config><InstanceName>Original</InstanceName></Config>");
                var database = Path.Combine(root, "candidate.db");
                var config = Path.Combine(root, "candidate.xml");
                File.WriteAllText(database, "candidate database");
                File.WriteAllText(config, $"<Config><EnableSsl>True</EnableSsl><SslCertPath>{Path.Combine(root, "missing.pfx")}</SslCertPath></Config>");

                var error = Assert.Throws<InvalidDataException>(() => FullRestoreBundle.Stage(info, database, config));

                Assert.Multiple(() =>
                {
                    Assert.That(error.Message, Does.Contain("certificate file is unavailable"));
                    Assert.That(File.ReadAllText(info.GetDatabase()), Is.EqualTo("original database"));
                    Assert.That(File.ReadAllText(info.GetConfigPath()), Does.Contain("Original"));
                    Assert.That(Directory.Exists(Path.Combine(root, "restore-pending")), Is.False);
                });
            }
            finally
            {
                Directory.Delete(root, true);
            }
        }

        [Test]
        public void invalid_prepared_database_restores_both_original_files_before_returning_failure()
        {
            var root = Path.Combine(Path.GetTempPath(), "chaptarr-restore-invalid-" + Guid.NewGuid());
            Directory.CreateDirectory(root);
            var folders = new Mock<IAppFolderInfo>();
            folders.SetupGet(f => f.AppDataFolder).Returns(root);
            var info = folders.Object;
            try
            {
                File.WriteAllText(info.GetDatabase(), "original database");
                File.WriteAllText(info.GetConfigPath(), "<Config><InstanceName>Original</InstanceName></Config>");
                var database = Path.Combine(root, "invalid.db");
                var config = Path.Combine(root, "candidate.xml");
                File.WriteAllText(database, "not sqlite");
                File.WriteAllText(config, "<Config><InstanceName>Candidate</InstanceName></Config>");
                FullRestoreBundle.Stage(info, database, config);
                FullRestoreBundle.Prepare(info);
                var restore = new DatabaseRestorationService(new Mock<IDiskProvider>().Object, info);
                Assert.Throws<SqliteException>(() => restore.Restore());
                Assert.That(FullRestoreBundle.IsPrepared(info), Is.False);
                Assert.That(File.ReadAllText(info.GetDatabase()), Is.EqualTo("original database"));
                Assert.That(File.ReadAllText(info.GetConfigPath()), Does.Contain("Original"));
            }
            finally
            {
                if (FullRestoreBundle.IsPrepared(info)) { FullRestoreBundle.Rollback(info); }
                Directory.Delete(root, true);
            }
        }

        [TestCase(false)]
        [TestCase(true)]
        public void config_and_database_are_published_and_recovered_as_a_pair(bool commit)
        {
            var root = Path.Combine(Path.GetTempPath(), "chaptarr-restore-test-" + Guid.NewGuid());
            Directory.CreateDirectory(root);
            var folders = new Mock<IAppFolderInfo>();
            folders.SetupGet(f => f.AppDataFolder).Returns(root);
            var info = folders.Object;
            try
            {
                File.WriteAllText(info.GetDatabase(), "original database");
                File.WriteAllText(info.GetConfigPath(), "<Config><InstanceName>Original</InstanceName></Config>");
                var candidate = Path.Combine(root, "candidate.db");
                var config = Path.Combine(root, "candidate.xml");
                File.WriteAllText(candidate, "candidate database");
                File.WriteAllText(config, "<Config><InstanceName>Candidate</InstanceName></Config>");
                FullRestoreBundle.Stage(info, candidate, config);
                Assert.That(File.ReadAllText(info.GetDatabase()), Is.EqualTo("original database"));
                Assert.That(File.ReadAllText(info.GetConfigPath()), Does.Contain("Original"));
                FullRestoreBundle.Prepare(info);
                Assert.That(File.ReadAllText(info.GetDatabase()), Is.EqualTo("candidate database"));
                Assert.That(File.ReadAllText(info.GetConfigPath()), Does.Contain("Candidate"));
                if (commit)
                {
                    Assert.Throws<InvalidOperationException>(() => FullRestoreBundle.CommitAfterStartup(info));
                    new DatabaseRestorationService(new Mock<IDiskProvider>().Object, info).Commit();
                    Assert.That(FullRestoreBundle.IsPrepared(info), Is.True, "Database success must retain the originals until host startup succeeds.");
                    FullRestoreBundle.CommitAfterStartup(info);
                }
                else { FullRestoreBundle.Rollback(info); }
                Assert.That(File.ReadAllText(info.GetDatabase()), Is.EqualTo(commit ? "candidate database" : "original database"));
                Assert.That(File.ReadAllText(info.GetConfigPath()), Does.Contain(commit ? "Candidate" : "Original"));
            }
            finally
            {
                if (FullRestoreBundle.IsPrepared(info)) { FullRestoreBundle.Rollback(info); }
                Directory.Delete(root, true);
            }
        }
    }
}

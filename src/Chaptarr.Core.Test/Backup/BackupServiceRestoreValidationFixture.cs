using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Abstractions;
using System.IO.Compression;
using System.Linq;
using System.Reflection;
using Microsoft.Data.Sqlite;
using NLog;
using NUnit.Framework;
using NzbDrone.Common;
using NzbDrone.Common.Disk;
using NzbDrone.Common.EnvironmentInfo;
using NzbDrone.Common.Extensions;
using NzbDrone.Core.Backup;
using NzbDrone.Core.Configuration;
using NzbDrone.Core.Datastore;

namespace Chaptarr.Core.Test.Backup
{
    [TestFixture]
    public class BackupServiceRestoreValidationFixture
    {
        private sealed class TestDiskProvider : DiskProviderBase
        {
            public TestDiskProvider(IFileSystem fileSystem)
                : base(fileSystem)
            {
            }

            public override long? GetAvailableSpace(string path) => throw new NotImplementedException();
            public override void InheritFolderPermissions(string filename) => throw new NotImplementedException();
            public override void SetEveryonePermissions(string filename) => throw new NotImplementedException();
            public override void SetFilePermissions(string path, string mask, string group) => throw new NotImplementedException();
            public override void SetPermissions(string path, string mask, string group) => throw new NotImplementedException();
            public override void CopyPermissions(string sourcePath, string targetPath) => throw new NotImplementedException();
            public override long? GetTotalSize(string path) => throw new NotImplementedException();
            public override bool TryCreateHardLink(string source, string destination) => throw new NotImplementedException();
        }

        private sealed class TestAppFolderInfo : IAppFolderInfo
        {
            public TestAppFolderInfo(string appDataFolder)
            {
                AppDataFolder = appDataFolder;
                TempFolder = appDataFolder;
                StartUpFolder = appDataFolder;
            }

            public string AppDataFolder { get; }
            public string TempFolder { get; }
            public string StartUpFolder { get; }
        }

        private sealed class TestArchiveService : IArchiveService
        {
            public Action<string> ExtractContents { get; set; }

            public void Extract(string compressedFile, string destination)
            {
                ZipFile.ExtractToDirectory(compressedFile, destination);
                if (ExtractContents != null)
                {
                    ExtractContents(destination);
                }
            }

            public void CreateZip(string path, IEnumerable<string> files)
            {
                using var archive = ZipFile.Open(path, ZipArchiveMode.Create);

                foreach (var file in files)
                {
                    archive.CreateEntryFromFile(file, Path.GetFileName(file));
                }
            }
        }

        private sealed class TestDiskTransferService : IDiskTransferService
        {
            public TransferMode TransferFolder(string sourcePath, string targetPath, TransferMode mode) => throw new NotImplementedException();

            public TransferMode TransferFile(string sourcePath, string targetPath, TransferMode mode, bool overwrite = false)
            {
                File.Copy(sourcePath, targetPath, overwrite);
                return TransferMode.Copy;
            }

            public int MirrorFolder(string sourcePath, string targetPath) => throw new NotImplementedException();
        }

        private sealed class RejectingRestoreDatabase : IRestoreDatabase
        {
            public List<string> ValidatedPaths { get; } = new();

            public void Validate(string path)
            {
                ValidatedPaths.Add(path);
                throw new InvalidDataException("invalid restore");
            }

            public bool Restore() => throw new NotImplementedException();
            public void Commit() => throw new NotImplementedException();
            public void Rollback() => throw new NotImplementedException();
        }

        private class ThrowingProxy<T> : DispatchProxy where T : class
        {
            protected override object Invoke(MethodInfo targetMethod, object[] args)
            {
                throw new NotImplementedException($"Test proxy does not implement {typeof(T).Name}.{targetMethod?.Name}");
            }
        }

        private string _tempFolder;
        private TestAppFolderInfo _appFolderInfo;
        private TestArchiveService _archiveService;
        private RejectingRestoreDatabase _restoreDatabase;
        private BackupService _subject;

        [SetUp]
        public void SetUp()
        {
            _tempFolder = Path.Combine(TestContext.CurrentContext.WorkDirectory, $"backup_restore_{Guid.NewGuid():N}");
            Directory.CreateDirectory(_tempFolder);
            _appFolderInfo = new TestAppFolderInfo(_tempFolder);
            _archiveService = new TestArchiveService();
            _restoreDatabase = new RejectingRestoreDatabase();
            _subject = CreateSubject(_restoreDatabase);
        }

        private BackupService CreateSubject(IRestoreDatabase restoreDatabase)
        {
            _subject = new BackupService(
                new MainDatabase(null),
                DispatchProxy.Create<IMakeDatabaseBackup, ThrowingProxy<IMakeDatabaseBackup>>(),
                DispatchProxy.Create<IDiskTransferService, ThrowingProxy<IDiskTransferService>>(),
                new TestDiskProvider(new FileSystem()),
                _appFolderInfo,
                _archiveService,
                DispatchProxy.Create<IConfigService, ThrowingProxy<IConfigService>>(),
                restoreDatabase,
                LogManager.GetCurrentClassLogger());
            return _subject;
        }

        private string CreateBackupArchive(string archiveName, bool includeInvalidDatabase)
        {
            var sourceFolder = Path.Combine(_tempFolder, "archive-source");
            Directory.CreateDirectory(sourceFolder);
            var configPath = Path.Combine(sourceFolder, "Config.xml");
            var databasePath = Path.Combine(sourceFolder, "readarr.db");
            var archivePath = Path.Combine(_tempFolder, archiveName);
            File.WriteAllText(configPath, "<Config><InstanceName>Replacement</InstanceName></Config>");

            var files = new List<string> { configPath };
            if (includeInvalidDatabase)
            {
                File.WriteAllText(databasePath, "invalid");
                files.Add(databasePath);
            }

            try
            {
                _archiveService.CreateZip(archivePath, files);
            }
            finally
            {
                Directory.Delete(sourceFolder, true);
            }

            return archivePath;
        }

        [TearDown]
        public void TearDown()
        {
            if (Directory.Exists(_tempFolder))
            {
                Directory.Delete(_tempFolder, true);
            }
        }

        [Test]
        public void should_validate_extracted_database_before_replacing_config()
        {
            var archivePath = CreateBackupArchive("backup.zip", includeInvalidDatabase: true);
            var configPath = _appFolderInfo.GetConfigPath();
            File.WriteAllText(configPath, "original");

            Assert.Throws<RestoreBackupFailedException>(() => _subject.Restore(archivePath));

            Assert.Multiple(() =>
            {
                Assert.That(File.ReadAllText(configPath), Is.EqualTo("original"));
                Assert.That(File.Exists(_appFolderInfo.GetDatabaseRestore()), Is.False);
                Assert.That(_restoreDatabase.ValidatedPaths, Has.Exactly(1).Items);
            });
        }

        [Test]
        public void should_validate_raw_database_before_staging_restore()
        {
            var uploadPath = Path.Combine(_tempFolder, "uploaded.db");
            File.WriteAllText(uploadPath, "invalid");

            Assert.Throws<RestoreBackupFailedException>(() => _subject.Restore(uploadPath));

            Assert.Multiple(() =>
            {
                Assert.That(File.ReadAllText(uploadPath), Is.EqualTo("invalid"));
                Assert.That(File.Exists(_appFolderInfo.GetDatabaseRestore()), Is.False);
                Assert.That(_restoreDatabase.ValidatedPaths, Is.EqualTo(new[] { uploadPath }));
            });
        }

        [Test]
        public void should_create_a_temporary_backup_with_private_staging()
        {
            var configPath = _appFolderInfo.GetConfigPath();
            File.WriteAllText(configPath, "config backup");

            var databasePath = Path.Combine(_tempFolder, "chaptarr.db");
            var databaseConnectionString = new SqliteConnectionStringBuilder { DataSource = databasePath }.ToString();
            var database = new Database("test", () => new SqliteConnection(databaseConnectionString));
            using (var connection = database.OpenConnection())
            {
                connection.Open();
                using var command = connection.CreateCommand();
                command.CommandText = "CREATE TABLE BackupFixture (Id INTEGER PRIMARY KEY)";
                command.ExecuteNonQuery();
            }

            var service = new BackupService(
                new MainDatabase(database),
                new MakeDatabaseBackup(LogManager.GetCurrentClassLogger()),
                new TestDiskTransferService(),
                new TestDiskProvider(new FileSystem()),
                _appFolderInfo,
                new TestArchiveService(),
                DispatchProxy.Create<IConfigService, ThrowingProxy<IConfigService>>(),
                _restoreDatabase,
                LogManager.GetCurrentClassLogger());

            var archivePath = service.CreateTemporaryBackup();

            using var archive = ZipFile.OpenRead(archivePath);
            Assert.Multiple(() =>
            {
                Assert.That(archive.GetEntry(Path.GetFileName(configPath)), Is.Not.Null);
                Assert.That(archive.GetEntry("chaptarr.db"), Is.Not.Null);
                Assert.That(archive.GetEntry("INFO"), Is.Not.Null);
                Assert.That(Directory.GetDirectories(Path.GetDirectoryName(archivePath)), Is.Empty);
            });
        }

        [Test]
        public void should_stage_a_supported_bookshelf_database_from_a_legacy_zip_backup()
        {
            var archivePath = CreateBackupArchive("readarr_backup_v0.4.21.71_2026.10.19_12.00.00.zip", includeInvalidDatabase: false);
            _archiveService.ExtractContents = destination => CreateBookshelfDatabase(Path.Combine(destination, "readarr.db"));
            _subject = CreateSubject(new DatabaseRestorationService(new TestDiskProvider(new FileSystem()), _appFolderInfo));

            Assert.That(BackupService.BackupFileRegex.IsMatch(Path.GetFileName(archivePath)), Is.True);
            File.WriteAllText(_appFolderInfo.GetConfigPath(), "original");
            _subject.Restore(archivePath);

            var restoredConnectionString = new SqliteConnectionStringBuilder
            {
                DataSource = Path.Combine(_appFolderInfo.AppDataFolder, "restore-pending", "database"),
                Mode = SqliteOpenMode.ReadOnly,
                Pooling = false
            }.ToString();

            Assert.Multiple(() =>
            {
                Assert.That(File.ReadAllText(_appFolderInfo.GetConfigPath()), Is.EqualTo("original"));
                Assert.That(File.ReadAllText(Path.Combine(_appFolderInfo.AppDataFolder, "restore-pending", "config")), Does.Contain("Replacement"));
                Assert.That(DatabaseLineageGuard.Detect(restoredConnectionString, DatabaseType.SQLite), Is.EqualTo(DatabaseLineage.BookshelfNG));
                Assert.That(File.Exists(archivePath), Is.True);
            });
        }

        [TestCase(".db")]
        [TestCase(".xml")]
        public void should_validate_and_stage_a_supported_bookshelf_database_from_a_raw_backup(string extension)
        {
            var backupPath = Path.Combine(_tempFolder, $"bookshelf_backup{extension}");
            CreateBookshelfDatabase(backupPath);
            _subject = CreateSubject(new DatabaseRestorationService(new TestDiskProvider(new FileSystem()), _appFolderInfo));

            _subject.Restore(backupPath);

            var restoredConnectionString = new SqliteConnectionStringBuilder
            {
                DataSource = _appFolderInfo.GetDatabaseRestore(),
                Mode = SqliteOpenMode.ReadOnly,
                Pooling = false
            }.ToString();

            Assert.Multiple(() =>
            {
                Assert.That(DatabaseLineageGuard.Detect(restoredConnectionString, DatabaseType.SQLite), Is.EqualTo(DatabaseLineage.BookshelfNG));
                Assert.That(File.Exists(_appFolderInfo.GetDatabaseRestore()), Is.True);
                Assert.That(File.Exists(backupPath), Is.False);
            });
        }

        private static void CreateBookshelfDatabase(string path)
        {
            var assembly = Assembly.GetExecutingAssembly();
            var resourceName = assembly.GetManifestResourceNames().Single(name => name.EndsWith("BookshelfNG.Schema.158.sql", StringComparison.Ordinal));
            using var schema = assembly.GetManifestResourceStream(resourceName);
            using var reader = new StreamReader(schema);
            using var connection = new SqliteConnection(new SqliteConnectionStringBuilder
            {
                DataSource = path,
                Mode = SqliteOpenMode.ReadWriteCreate,
                Pooling = false
            }.ToString());
            connection.Open();
            using var command = connection.CreateCommand();
            command.CommandText = reader.ReadToEnd();
            command.ExecuteNonQuery();
            command.CommandText = @"
                WITH RECURSIVE migrations(version) AS
                (
                    SELECT 1 UNION ALL SELECT version + 1 FROM migrations WHERE version < 158
                )
                INSERT INTO VersionInfo (Version, AppliedOn, Description)
                SELECT version, CURRENT_TIMESTAMP, 'restore fixture' FROM migrations;";
            command.ExecuteNonQuery();
        }
    }
}

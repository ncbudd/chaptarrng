using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Xml;
using System.Xml.Linq;
using NzbDrone.Common.EnvironmentInfo;
using NzbDrone.Common.Extensions;

namespace NzbDrone.Core.Datastore
{
    // A durable journal for the config/database pair. Prepared bundles are applied before the
    // host reads config.xml; startup migrations either commit the pair or restore both originals.
    public static class FullRestoreBundle
    {
        private static readonly object Sync = new object();
        private static readonly HashSet<string> Prepared = new HashSet<string>(StringComparer.Ordinal);
        private static readonly HashSet<string> Validated = new HashSet<string>(StringComparer.Ordinal);
        private static string Pending(IAppFolderInfo folders) => Path.Combine(folders.AppDataFolder, "restore-pending");
        private static string Working(IAppFolderInfo folders) => Path.Combine(folders.AppDataFolder, "restore-in-progress");

        public static bool IsPrepared(IAppFolderInfo folders)
        {
            lock (Sync) { return Prepared.Contains(Working(folders)); }
        }

        public static bool HasIncompleteRestore(IAppFolderInfo folders)
        {
            return Directory.Exists(Working(folders));
        }

        public static void Stage(IAppFolderInfo folders, string database, string config)
        {
            lock (Sync)
            {
                if (Directory.Exists(Pending(folders)) || Directory.Exists(Working(folders)))
                {
                    throw new IOException("A full restore is already pending. Restart before requesting another restore.");
                }

                if (config != null)
                {
                    using var reader = XmlReader.Create(config, new XmlReaderSettings { DtdProcessing = DtdProcessing.Prohibit, XmlResolver = null, MaxCharactersInDocument = 2 * 1024 * 1024 });
                    var document = XDocument.Load(reader);
                    if (document.Root?.Name.LocalName != "Config" ||
                        document.Root.Elements().Any(e => e.Name.LocalName.Equals("PostgresHost", StringComparison.OrdinalIgnoreCase) && !string.IsNullOrWhiteSpace(e.Value)))
                    {
                        throw new InvalidDataException("The restore config must be a valid SQLite Config document.");
                    }

                    var sslEnabled = document.Root.Elements().FirstOrDefault(e => e.Name.LocalName.Equals("EnableSsl", StringComparison.OrdinalIgnoreCase))?.Value;
                    if (bool.TryParse(sslEnabled, out var enableSsl) && enableSsl)
                    {
                        var certificate = document.Root.Elements().FirstOrDefault(e => e.Name.LocalName.Equals("SslCertPath", StringComparison.OrdinalIgnoreCase))?.Value;
                        if (string.IsNullOrWhiteSpace(certificate) || !File.Exists(certificate))
                        {
                            throw new InvalidDataException("The backup enables SSL, but its certificate file is unavailable on this installation.");
                        }
                    }
                }

                var staging = Path.Combine(folders.AppDataFolder, ".restore-stage-" + Guid.NewGuid().ToString("N"));
                CreatePrivateDirectory(staging);
                try
                {
                    CopyDurably(database, Path.Combine(staging, "database"));
                    if (config != null) { CopyDurably(config, Path.Combine(staging, "config")); }
                    Directory.Move(staging, Pending(folders));
                }
                finally
                {
                    if (Directory.Exists(staging)) { Directory.Delete(staging, true); }
                }
            }
        }

        public static void Prepare(IAppFolderInfo folders)
        {
            lock (Sync)
            {
                var work = Working(folders);
                if (Prepared.Contains(work)) { return; }
                if (Directory.Exists(work))
                {
                    RollbackFiles(folders);
                    Quarantine(work);
                }

                if (!Directory.Exists(Pending(folders))) { return; }
                Directory.Move(Pending(folders), work);
                try
                {
                    var originals = Path.Combine(work, "originals");
                    CreatePrivateDirectory(originals);
                    var existing = new List<string>();
                    var paths = ActivePaths(folders);
                    for (var i = 0; i < paths.Length; i++)
                    {
                        if (!File.Exists(paths[i])) { continue; }
                        CopyDurably(paths[i], Path.Combine(originals, i.ToString(System.Globalization.CultureInfo.InvariantCulture)));
                        existing.Add(i.ToString(System.Globalization.CultureInfo.InvariantCulture));
                    }

                    WriteDurably(Path.Combine(work, "original-files.json"), JsonSerializer.SerializeToUtf8Bytes(existing));
                    WriteDurably(Path.Combine(work, "backup-complete"), Array.Empty<byte>());
                    foreach (var sidecar in paths.Skip(1).Take(3)) { File.Delete(sidecar); }
                    File.Move(Path.Combine(work, "database"), folders.GetDatabase(), true);
                    if (File.Exists(Path.Combine(work, "config"))) { File.Move(Path.Combine(work, "config"), folders.GetConfigPath(), true); }
                    Prepared.Add(work);
                }
                catch
                {
                    RollbackFiles(folders);
                    Quarantine(work);
                    throw;
                }
            }
        }

        public static void MarkDatabaseValidated(IAppFolderInfo folders)
        {
            lock (Sync)
            {
                if (Prepared.Contains(Working(folders))) { Validated.Add(Working(folders)); }
            }
        }

        public static void CommitAfterStartup(IAppFolderInfo folders)
        {
            lock (Sync)
            {
                if (!Prepared.Contains(Working(folders))) { return; }
                if (!Validated.Contains(Working(folders)))
                {
                    throw new InvalidOperationException("A full restore cannot commit before database validation and migration.");
                }

                Commit(folders);
            }
        }

        public static void Commit(IAppFolderInfo folders)
        {
            lock (Sync)
            {
                var work = Working(folders);
                if (!Prepared.Contains(work)) { return; }
                // Renaming is the commit marker. Cleanup can be repeated safely after a crash.
                var committed = work + ".committed-" + Guid.NewGuid().ToString("N");
                Directory.Move(work, committed);
                Prepared.Remove(work);
                Validated.Remove(work);
                // A cleanup failure must not roll back an already committed pair.
                try { Directory.Delete(committed, true); }
                catch (IOException) { }
                catch (UnauthorizedAccessException) { }
            }
        }

        public static void Rollback(IAppFolderInfo folders)
        {
            lock (Sync)
            {
                Prepared.Remove(Working(folders));
                Validated.Remove(Working(folders));
                RollbackFiles(folders);
                if (Directory.Exists(Working(folders))) { Quarantine(Working(folders)); }
            }
        }

        private static void RollbackFiles(IAppFolderInfo folders)
        {
            var work = Working(folders);
            if (!File.Exists(Path.Combine(work, "backup-complete"))) { return; }
            var originals = JsonSerializer.Deserialize<HashSet<string>>(File.ReadAllText(Path.Combine(work, "original-files.json")));
            var paths = ActivePaths(folders);
            for (var i = 0; i < paths.Length; i++)
            {
                var key = i.ToString(System.Globalization.CultureInfo.InvariantCulture);
                if (originals.Contains(key))
                {
                    var temporary = paths[i] + ".restore-recovery";
                    CopyDurably(Path.Combine(work, "originals", key), temporary);
                    File.Move(temporary, paths[i], true);
                }
                else { File.Delete(paths[i]); }
            }
        }

        private static string[] ActivePaths(IAppFolderInfo folders) => new[]
        {
            folders.GetDatabase(), folders.GetDatabase() + "-shm", folders.GetDatabase() + "-wal",
            folders.GetDatabase() + "-journal", folders.GetConfigPath()
        };

        private static void CreatePrivateDirectory(string path)
        {
            if (OperatingSystem.IsWindows()) { Directory.CreateDirectory(path); }
            else { Directory.CreateDirectory(path, UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.UserExecute); }
        }

        private static void CopyDurably(string source, string destination)
        {
            using var input = File.OpenRead(source);
            using var output = new FileStream(destination, FileMode.Create, FileAccess.Write, FileShare.None);
            input.CopyTo(output);
            output.Flush(true);
        }

        private static void WriteDurably(string path, byte[] contents)
        {
            using var file = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None);
            file.Write(contents);
            file.Flush(true);
        }

        private static void Quarantine(string path) => Directory.Move(path, path + ".failed-" + Guid.NewGuid().ToString("N"));
    }
}

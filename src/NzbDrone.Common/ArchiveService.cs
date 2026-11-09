using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Diagnostics;
using System.Linq;
using ICSharpCode.SharpZipLib.Checksum;
using ICSharpCode.SharpZipLib.GZip;
using ICSharpCode.SharpZipLib.Tar;
using ICSharpCode.SharpZipLib.Zip;
using NLog;

namespace NzbDrone.Common
{
    internal static class ArchiveExtractionLimits
    {
        internal const int DefaultMaxEntries = 20_000;
        internal const long DefaultMaxSingleEntryBytes = 512L * 1024 * 1024; // 512 MiB
        internal const long DefaultMaxTotalBytes = 1024L * 1024 * 1024; // 1 GiB

        internal static int MaxEntries { get; set; } = DefaultMaxEntries;
        internal static long MaxSingleEntryBytes { get; set; } = DefaultMaxSingleEntryBytes;
        internal static long MaxTotalBytes { get; set; } = DefaultMaxTotalBytes;
    }

    public sealed class ArchiveExtractionOptions
    {
        public int MaxEntries { get; init; } = 20_000;
        public long MaxSingleEntryBytes { get; init; }
        public long MaxTotalBytes { get; init; }
        public TimeSpan Timeout { get; init; } = TimeSpan.FromMinutes(30);
        public static ArchiveExtractionOptions Media => new() { MaxSingleEntryBytes = 16L << 30, MaxTotalBytes = 128L << 30 };
        public static ArchiveExtractionOptions Backup => new() { MaxSingleEntryBytes = 32L << 30, MaxTotalBytes = 64L << 30 };
        public static ArchiveExtractionOptions Update => new() { MaxSingleEntryBytes = 2L << 30, MaxTotalBytes = 4L << 30 };
    }

    public interface IArchiveService
    {
        void Extract(string compressedFile, string destination);
        void Extract(string compressedFile, string destination, ArchiveExtractionOptions options) => Extract(compressedFile, destination);
        void CreateZip(string path, IEnumerable<string> files);
    }

    public class ArchiveService : IArchiveService
    {
        private readonly Logger _logger;

        public ArchiveService(Logger logger)
        {
            _logger = logger;
        }

        public void Extract(string compressedFile, string destination)
        {
            Extract(compressedFile, destination, new ArchiveExtractionOptions
            {
                MaxEntries = ArchiveExtractionLimits.MaxEntries,
                MaxSingleEntryBytes = ArchiveExtractionLimits.MaxSingleEntryBytes,
                MaxTotalBytes = ArchiveExtractionLimits.MaxTotalBytes
            });
        }

        public void Extract(string compressedFile, string destination, ArchiveExtractionOptions options)
        {
            ArgumentNullException.ThrowIfNull(options);
            if (options.MaxEntries <= 0 || options.MaxSingleEntryBytes <= 0 || options.MaxTotalBytes <= 0 || options.Timeout <= TimeSpan.Zero)
            {
                throw new ArgumentOutOfRangeException(nameof(options));
            }

            destination = Path.GetFullPath(destination);
            RejectLinkedAncestors(destination);
            if (File.Exists(destination) || (Directory.Exists(destination) && Directory.EnumerateFileSystemEntries(destination).Any()))
            {
                throw new IOException("Archive destination must be a new or empty directory.");
            }

            var parent = Path.GetDirectoryName(destination);
            Directory.CreateDirectory(parent);
            var stage = Path.Combine(parent, ".chaptarr-extract-" + Guid.NewGuid().ToString("N"));
            if (OperatingSystem.IsWindows())
            {
                Directory.CreateDirectory(stage);
            }
            else
            {
                Directory.CreateDirectory(stage, UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.UserExecute);
            }

            try
            {
                if (compressedFile.EndsWith(".zip", StringComparison.OrdinalIgnoreCase))
                {
                    ExtractZip(compressedFile, stage, options);
                }
                else
                {
                    ExtractTgz(compressedFile, stage, options);
                }

                RejectLinkedAncestors(destination);
                if (Directory.Exists(destination))
                {
                    Directory.Delete(destination, false);
                }

                Directory.Move(stage, destination);
            }
            finally
            {
                if (Directory.Exists(stage))
                {
                    Directory.Delete(stage, true);
                }
            }
        }

        private static void RejectLinkedAncestors(string path)
        {
            for (var current = path; !string.IsNullOrEmpty(current); current = Path.GetDirectoryName(current))
            {
                var info = new DirectoryInfo(current);
                if (info.LinkTarget != null || (info.Exists && (info.Attributes & FileAttributes.ReparsePoint) != 0))
                {
                    throw new IOException("Archive destination must not traverse a link or reparse point.");
                }
            }
        }

        public void CreateZip(string path, IEnumerable<string> files)
        {
            _logger.Debug("Creating archive {0}", path);

            using var zipFile = ZipFile.Create(path);

            zipFile.BeginUpdate();

            var backupLimits = ArchiveExtractionOptions.Backup;
            long totalBytes = 0;
            var count = 0;
            foreach (var file in files)
            {
                var size = new FileInfo(file).Length;
                totalBytes += size;
                if (++count > backupLimits.MaxEntries || size > backupLimits.MaxSingleEntryBytes || totalBytes > backupLimits.MaxTotalBytes)
                {
                    throw new IOException("Backup exceeds the supported restore size budget.");
                }

                zipFile.Add(file, Path.GetFileName(file));
            }

            zipFile.CommitUpdate();
        }

        private void ExtractZip(string compressedFile, string destination, ArchiveExtractionOptions options)
        {
            Directory.CreateDirectory(destination);
            var destinationRoot = GetSafeExtractionRoot(destination);

            using var fileStream = File.OpenRead(compressedFile);
            using var zipFile = new ZipFile(fileStream);

            // Validate the complete directory before reading any compressed payload. TestArchive(true)
            // would decompress every entry before enforcing the budgets.
            if (zipFile.Count > options.MaxEntries)
            {
                throw new IOException("Archive contains too many entries.");
            }

            long declaredTotal = 0;
            var paths = new HashSet<string>(OperatingSystem.IsWindows() ? StringComparer.OrdinalIgnoreCase : StringComparer.Ordinal);
            foreach (ZipEntry entry in zipFile)
            {
                var path = GetSafeExtractionPath(destinationRoot, entry.Name);
                if (!paths.Add(path) || entry.IsCrypted || ((entry.ExternalFileAttributes >> 16) & 0xf000) == 0xa000)
                {
                    throw new IOException("Duplicate, encrypted, or linked archive entry is not supported.");
                }

                if (entry.Size < 0 || entry.Size > options.MaxSingleEntryBytes || entry.Size > options.MaxTotalBytes - declaredTotal)
                {
                    throw new IOException("Archive exceeds its declared size budget.");
                }

                declaredTotal += entry.Size;
            }

            var timer = Stopwatch.StartNew();
            var entryCount = 0;
            long totalExtractedBytes = 0;

            foreach (ZipEntry zipEntry in zipFile)
            {
                entryCount++;
                if (entryCount > options.MaxEntries)
                {
                    throw new IOException($"Archive contains too many entries (limit {options.MaxEntries})");
                }

                if (!zipEntry.IsFile)
                {
                    continue; // Ignore directories
                }

                var entryFileName = zipEntry.Name;

                if (zipEntry.Size > options.MaxSingleEntryBytes)
                {
                    throw new IOException($"Archive entry '{entryFileName}' exceeds maximum allowed size (limit {options.MaxSingleEntryBytes} bytes)");
                }

                if (zipEntry.Size >= 0 && totalExtractedBytes + zipEntry.Size > options.MaxTotalBytes)
                {
                    throw new IOException($"Archive exceeds maximum allowed extracted size (limit {options.MaxTotalBytes} bytes)");
                }

                var fullZipToPath = GetSafeExtractionPath(destinationRoot, entryFileName);
                var directoryName = Path.GetDirectoryName(fullZipToPath);
                if (!string.IsNullOrWhiteSpace(directoryName))
                {
                    Directory.CreateDirectory(directoryName);
                }

                using var zipStream = zipFile.GetInputStream(zipEntry);
                using var streamWriter = new FileStream(fullZipToPath, FileMode.CreateNew, FileAccess.Write, FileShare.None);
                var crc = new Crc32();
                CopyStreamWithLimits(zipStream, streamWriter, entryFileName, options.MaxSingleEntryBytes, ref totalExtractedBytes, options.MaxTotalBytes, timer, options.Timeout, crc);
                if (crc.Value != zipEntry.Crc)
                {
                    throw new IOException("Archive entry failed CRC validation.");
                }
            }
        }

        private void ExtractTgz(string compressedFile, string destination, ArchiveExtractionOptions options)
        {
            Directory.CreateDirectory(destination);
            var destinationRoot = GetSafeExtractionRoot(destination);

            using var inStream = File.OpenRead(compressedFile);
            using var gzipStream = new GZipInputStream(inStream);
            using var tarStream = new TarInputStream(gzipStream, Encoding.UTF8);

            var entryCount = 0;
            long totalExtractedBytes = 0;

            var timer = Stopwatch.StartNew();
            TarEntry entry;
            while ((entry = tarStream.GetNextEntry()) != null)
            {
                if (string.IsNullOrWhiteSpace(entry.Name))
                {
                    continue;
                }

                entryCount++;
                if (entryCount > options.MaxEntries)
                {
                    throw new IOException($"Archive contains too many entries (limit {options.MaxEntries})");
                }

                var typeFlag = entry.TarHeader.TypeFlag;

                if (typeFlag == TarHeader.LF_LINK || typeFlag == TarHeader.LF_SYMLINK)
                {
                    throw new IOException($"Unsupported archive entry type (link): '{entry.Name}'");
                }

                if (entry.Size < 0)
                {
                    throw new IOException($"Invalid archive entry size for '{entry.Name}'");
                }

                if (entry.Size > options.MaxSingleEntryBytes)
                {
                    throw new IOException($"Archive entry '{entry.Name}' exceeds maximum allowed size (limit {options.MaxSingleEntryBytes} bytes)");
                }

                if (totalExtractedBytes + entry.Size > options.MaxTotalBytes)
                {
                    throw new IOException($"Archive exceeds maximum allowed extracted size (limit {options.MaxTotalBytes} bytes)");
                }

                if (entry.IsDirectory)
                {
                    var fullPath = GetSafeExtractionPath(destinationRoot, entry.Name);
                    Directory.CreateDirectory(fullPath);
                    continue;
                }

                // Ignore tar metadata/extended headers and non-file types
                if (typeFlag != TarHeader.LF_NORMAL && typeFlag != TarHeader.LF_OLDNORM)
                {
                    CopyStreamWithLimits(tarStream, Stream.Null, entry.Name, options.MaxSingleEntryBytes, ref totalExtractedBytes, options.MaxTotalBytes, timer, options.Timeout);
                    continue;
                }

                var fullFilePath = GetSafeExtractionPath(destinationRoot, entry.Name);

                var directoryName = Path.GetDirectoryName(fullFilePath);
                if (!string.IsNullOrWhiteSpace(directoryName))
                {
                    Directory.CreateDirectory(directoryName);
                }

                using var outputStream = new FileStream(fullFilePath, FileMode.CreateNew, FileAccess.Write, FileShare.None);
                CopyStreamWithLimits(tarStream, outputStream, entry.Name, options.MaxSingleEntryBytes, ref totalExtractedBytes, options.MaxTotalBytes, timer, options.Timeout);
            }
        }

        private static void CopyStreamWithLimits(Stream input, Stream output, string entryName, long maxEntryBytes, ref long totalExtractedBytes, long maxTotalBytes, Stopwatch timer, TimeSpan timeout, Crc32 crc = null)
        {
            var buffer = new byte[81920];
            long entryBytes = 0;

            int read;
            while ((read = input.Read(buffer, 0, buffer.Length)) > 0)
            {
                if (timer.Elapsed > timeout)
                {
                    throw new IOException("Archive extraction exceeded its time budget.");
                }

                crc?.Update(new ArraySegment<byte>(buffer, 0, read));
                entryBytes += read;
                totalExtractedBytes += read;

                if (entryBytes > maxEntryBytes)
                {
                    throw new IOException($"Archive entry '{entryName}' exceeds maximum allowed size (limit {maxEntryBytes} bytes)");
                }

                if (totalExtractedBytes > maxTotalBytes)
                {
                    throw new IOException($"Archive exceeds maximum allowed extracted size (limit {maxTotalBytes} bytes)");
                }

                output.Write(buffer, 0, read);
            }
        }

        private static string GetSafeExtractionRoot(string destination)
        {
            var destinationFullPath = Path.GetFullPath(destination);
            if (!destinationFullPath.EndsWith(Path.DirectorySeparatorChar.ToString(), GetPathComparison()) &&
                !destinationFullPath.EndsWith(Path.AltDirectorySeparatorChar.ToString(), GetPathComparison()))
            {
                destinationFullPath += Path.DirectorySeparatorChar;
            }

            return destinationFullPath;
        }

        private static string GetSafeExtractionPath(string destinationRoot, string entryName)
        {
            var normalizedEntryName = entryName.Replace('\\', Path.DirectorySeparatorChar);
            var fullPath = Path.GetFullPath(Path.Combine(destinationRoot, normalizedEntryName));

            if (!fullPath.StartsWith(destinationRoot, GetPathComparison()))
            {
                throw new IOException($"Archive entry is trying to write outside destination folder: '{entryName}'");
            }

            return fullPath;
        }

        private static StringComparison GetPathComparison()
        {
            return Path.DirectorySeparatorChar == '\\' ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal;
        }

    }
}

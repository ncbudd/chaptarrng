using System;
using System.Collections.Generic;
using System.Linq;
using Moq;
using NLog;
using NUnit.Framework;
using NzbDrone.Common.Disk;
using NzbDrone.Common.Messaging;
using NzbDrone.Core.Books;
using NzbDrone.Core.Download;
using NzbDrone.Core.Download.TrackedDownloads;
using NzbDrone.Core.History;
using NzbDrone.Core.Indexers;
using NzbDrone.Core.MediaFiles;
using NzbDrone.Core.MediaFiles.BookImport;
using NzbDrone.Core.MediaFiles.Events;
using NzbDrone.Core.Messaging.Events;
using NzbDrone.Core.Parser.Model;
using NzbDrone.Core.Qualities;

namespace Chaptarr.Core.Test.Download
{
    [TestFixture]
    public class CompletedDownloadServiceDuplicateFixture
    {
        private const string OccupiedReason = ImportApprovedBooks.AdditionalCopyDestinationOccupiedRejectionPrefix + ": /books/Author/Title.epub. Current naming settings cannot represent a separate copy.";

        private sealed class RecordingEventAggregator : IEventAggregator
        {
            public List<IEvent> Events { get; } = new();

            public void PublishEvent<TEvent>(TEvent @event)
                where TEvent : class, IEvent
            {
                Events.Add(@event);
            }
        }

        private sealed class StubProvideImportItemService : IProvideImportItemService
        {
            public DownloadClientItem ProvideImportItem(DownloadClientItem item, DownloadClientItem previousImportAttempt)
            {
                var clone = item.Clone();
                clone.OutputPath = new OsPath("/tmp/chaptarr-duplicate");
                return clone;
            }
        }

        private sealed class StubImportService : IDownloadedBooksImportService
        {
            public List<ImportResult> Results { get; set; } = new();

            public List<ImportResult> ProcessPath(string path, ImportMode importMode = ImportMode.Auto, Author author = null, DownloadClientItem downloadClientItem = null, RemoteBook remoteBook = null, bool requireDefaultRootFolderForMissingAuthors = false)
                => Results;

            public List<ImportResult> ProcessFolder(string path, ImportMode importMode = ImportMode.Auto, Author author = null, DownloadClientItem downloadClientItem = null, RemoteBook remoteBook = null, bool requireDefaultRootFolderForMissingAuthors = false)
                => throw new NotImplementedException();

            public List<ImportResult> ProcessFile(string path, ImportMode importMode = ImportMode.Auto, Author author = null, DownloadClientItem downloadClientItem = null, RemoteBook remoteBook = null, bool requireDefaultRootFolderForMissingAuthors = false)
                => throw new NotImplementedException();
        }

        private sealed class PassthroughDownloadImportModeResolver : IDownloadImportModeResolver
        {
            public ImportMode Resolve(ImportMode requestedMode, DownloadClientItem downloadClientItem) => requestedMode;
            public DownloadImportPolicy ResolvePolicy(ImportMode requestedMode, DownloadClientItem downloadClientItem) => new(requestedMode, false);
            public bool ShouldPreserveDownloadClientItem(DownloadClientItem downloadClientItem) => false;
        }

        private sealed class StubAlreadyImported : ITrackedDownloadAlreadyImported
        {
            public bool IsImported(TrackedDownload trackedDownload, List<EntityHistory> historyItems) => false;
        }

        private static ImportResult Rejected(int bookId, params string[] errors)
        {
            var author = new Author { Id = 7, Name = "Test Author" };
            var book = new Book { Id = bookId, AuthorId = 7, Author = author, Title = "Title " + bookId, MediaType = BookMediaType.Ebook };
            var localBook = new LocalBook
            {
                Author = author,
                Book = book,
                Path = $"/tmp/chaptarr-duplicate/{bookId}.epub",
                Quality = new QualityModel(Quality.EPUB)
            };

            return new ImportResult(new ImportDecision<LocalBook>(localBook), errors);
        }

        private static EntityHistory Imported(int bookId, string downloadId)
        {
            return new EntityHistory
            {
                EventType = EntityHistoryEventType.BookFileImported,
                BookId = bookId,
                DownloadId = downloadId,
                Date = DateTime.UtcNow
            };
        }

        private static (CompletedDownloadService Subject, TrackedDownload Download, RecordingEventAggregator Events) Create(
            List<ImportResult> results,
            List<EntityHistory> bookHistory,
            DownloadProtocol protocol = DownloadProtocol.Usenet)
        {
            var events = new RecordingEventAggregator();
            var history = new Mock<IHistoryService>();
            history.Setup(h => h.FindByDownloadId(It.IsAny<string>())).Returns(new List<EntityHistory>());
            history.Setup(h => h.GetByBook(It.IsAny<int>(), EntityHistoryEventType.BookFileImported))
                   .Returns((int id, EntityHistoryEventType? _) => bookHistory.Where(h => h.BookId == id).ToList());

            var download = new TrackedDownload
            {
                DownloadClient = 1,
                DownloadItem = new DownloadClientItem
                {
                    DownloadId = "dup-download",
                    Title = "Duplicate.Release",
                    Status = DownloadItemStatus.Completed,
                    DownloadClientInfo = new DownloadClientItemClientInfo
                    {
                        Id = 1,
                        Name = "client",
                        Protocol = protocol
                    }
                },
                RemoteBook = new RemoteBook
                {
                    Author = new Author { Id = 7, Name = "Test Author" },
                    Books = results.Select(r => r.ImportDecision.Item.Book).ToList()
                },
                State = TrackedDownloadState.ImportPending
            };

            var subject = new CompletedDownloadService(
                events,
                history.Object,
                new StubProvideImportItemService(),
                new StubImportService { Results = results },
                new PassthroughDownloadImportModeResolver(),
                new StubAlreadyImported(),
                NoopFailedDownloadService.Instance,
                LogManager.GetCurrentClassLogger(),
                NoopDownloadClientFileSnapshotService.Instance);

            return (subject, download, events);
        }

        [Test, Platform(Exclude = "Win", Reason = "Test uses Unix paths")]
        public void should_mark_duplicate_of_book_imported_from_another_download_as_imported()
        {
            var (subject, download, events) = Create(
                new List<ImportResult> { Rejected(10, OccupiedReason) },
                new List<EntityHistory> { Imported(10, "other-download") });

            subject.Import(download);

            Assert.That(download.State, Is.EqualTo(TrackedDownloadState.Imported));
            Assert.That(download.StatusMessages, Is.Empty);
            Assert.That(events.Events, Has.One.InstanceOf<DownloadCompletedEvent>());
            Assert.That(events.Events, Has.None.InstanceOf<BookImportIncompleteEvent>());
        }

        [Test, Platform(Exclude = "Win", Reason = "Test uses Unix paths")]
        public void should_complete_duplicate_torrent_through_normal_completion_without_removing_it()
        {
            var (subject, download, events) = Create(
                new List<ImportResult> { Rejected(10, OccupiedReason) },
                new List<EntityHistory> { Imported(10, "other-download") },
                DownloadProtocol.Torrent);

            subject.Import(download);

            // Removal is left to the existing DownloadCompletedEvent handling, which honours CanBeRemoved
            // (still seeding) and the client's RemoveCompletedDownloads setting.
            Assert.That(download.State, Is.EqualTo(TrackedDownloadState.Imported));
            Assert.That(events.Events, Has.None.InstanceOf<DownloadCanBeRemovedEvent>());
            Assert.That(events.Events, Has.None.InstanceOf<DownloadFailedEvent>());
            Assert.That(events.Events.OfType<DownloadCompletedEvent>().Single().TrackedDownload, Is.SameAs(download));
        }

        [Test, Platform(Exclude = "Win", Reason = "Test uses Unix paths")]
        public void should_block_duplicate_rejection_when_book_has_no_file_imported_from_another_download()
        {
            var (subject, download, events) = Create(
                new List<ImportResult> { Rejected(10, OccupiedReason) },
                new List<EntityHistory>());

            subject.Import(download);

            Assert.That(download.State, Is.EqualTo(TrackedDownloadState.ImportBlocked));
            Assert.That(events.Events, Has.None.InstanceOf<DownloadCompletedEvent>());
            Assert.That(events.Events, Has.Some.InstanceOf<BookImportIncompleteEvent>());
        }

        [Test, Platform(Exclude = "Win", Reason = "Test uses Unix paths")]
        public void should_block_duplicate_rejection_when_only_import_is_from_the_same_download()
        {
            var (subject, download, events) = Create(
                new List<ImportResult> { Rejected(10, OccupiedReason) },
                new List<EntityHistory> { Imported(10, "DUP-DOWNLOAD") });

            subject.Import(download);

            Assert.That(download.State, Is.EqualTo(TrackedDownloadState.ImportBlocked));
            Assert.That(events.Events, Has.None.InstanceOf<DownloadCompletedEvent>());
        }

        [Test, Platform(Exclude = "Win", Reason = "Test uses Unix paths")]
        public void should_block_when_duplicate_rejection_is_mixed_with_another_rejection()
        {
            var (subject, download, events) = Create(
                new List<ImportResult>
                {
                    Rejected(10, OccupiedReason),
                    Rejected(11, "TAG_EXTRACTION_FAILED")
                },
                new List<EntityHistory> { Imported(10, "other-download"), Imported(11, "other-download") });

            subject.Import(download);

            Assert.That(download.State, Is.EqualTo(TrackedDownloadState.ImportBlocked));
            Assert.That(events.Events, Has.None.InstanceOf<DownloadCompletedEvent>());
            Assert.That(events.Events, Has.Some.InstanceOf<BookImportIncompleteEvent>());
        }

        [Test, Platform(Exclude = "Win", Reason = "Test uses Unix paths")]
        public void should_block_when_one_error_on_a_file_is_not_the_duplicate_reason()
        {
            var (subject, download, events) = Create(
                new List<ImportResult> { Rejected(10, OccupiedReason, "Import failed: boom") },
                new List<EntityHistory> { Imported(10, "other-download") });

            subject.Import(download);

            Assert.That(download.State, Is.EqualTo(TrackedDownloadState.ImportBlocked));
            Assert.That(events.Events, Has.None.InstanceOf<DownloadCompletedEvent>());
        }

        [Test, Platform(Exclude = "Win", Reason = "Test uses Unix paths")]
        public void should_block_when_second_book_has_no_import_from_another_download()
        {
            var (subject, download, events) = Create(
                new List<ImportResult>
                {
                    Rejected(10, OccupiedReason),
                    Rejected(11, OccupiedReason)
                },
                new List<EntityHistory> { Imported(10, "other-download") });

            subject.Import(download);

            Assert.That(download.State, Is.EqualTo(TrackedDownloadState.ImportBlocked));
            Assert.That(events.Events, Has.None.InstanceOf<DownloadCompletedEvent>());
        }
    }
}

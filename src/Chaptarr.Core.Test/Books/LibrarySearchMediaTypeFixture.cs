using System;
using System.Data;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Dapper;
using Microsoft.Data.Sqlite;
using Npgsql;
using NUnit.Framework;
using NLog;
using NzbDrone.Core.Books;
using NzbDrone.Core.Books.Services;
using NzbDrone.Core.Datastore;
using NzbDrone.Core.MediaCover;
using Chaptarr.Api.V1.Search;
using MediaCoverModel = NzbDrone.Core.MediaCover.MediaCover;

namespace Chaptarr.Core.Test.Books
{
    [TestFixture]
    public class LibrarySearchMediaTypeFixture
    {
        private sealed class NoOpCoverMapper : IMapCoversToLocal
        {
            public void ConvertToLocalUrls(int entityId, MediaCoverEntity coverEntity, System.Collections.Generic.IEnumerable<MediaCoverModel> covers, string selectedAuthorImageHash = null)
            {
            }

            public string GetCoverPath(int entityId, MediaCoverEntity coverEntity, MediaCoverTypes coverType, string extension, int? height = null) => null;
            public void EnsureAuthorCovers(Author author) { }
            public void EnsureBookCovers(Book book) { }
            public Task<EnsureImageResult> EnsureAuthorImage(Author author, MediaCoverModel cover) => Task.FromResult<EnsureImageResult>(null);
        }

        [OneTimeSetUp]
        public void OneTimeSetUp()
        {
            if (TableMapping.Mapper.TableMap.Count == 0)
            {
                TableMapping.Map();
            }
        }

        [Test]
        public void omitted_media_type_returns_both_formats_grouped_together()
        {
            WithController(controller =>
            {
                var result = controller.Search("Winter", 10);

                var sharedWork = result.Books.Single(book => book.Id == 10);
                Assert.That(sharedWork.LocalAudiobookBooks.Select(book => book.Id), Is.EqualTo(new[] { 10 }));
                Assert.That(sharedWork.LocalEbookBooks.Select(book => book.Id), Is.EqualTo(new[] { 11 }));
                Assert.That(result.Books.Count, Is.EqualTo(2));
                Assert.That(result.Authors.Select(author => author.Id).OrderBy(id => id), Is.EqualTo(new[] { 1, 2 }));
            });
        }

        [Test]
        public void ebook_media_type_returns_only_ebook_books_and_authors_with_ebooks()
        {
            WithController(controller =>
            {
                var result = controller.Search("Winter", 10, "ebook");

                Assert.That(result.Books, Has.Count.EqualTo(1));
                Assert.That(result.Books[0].LocalEbookBooks.Select(book => book.Id), Is.EqualTo(new[] { 11 }));
                Assert.That(result.Books[0].LocalAudiobookBooks, Is.Empty);
                Assert.That(result.Authors.Select(author => author.Id), Is.EqualTo(new[] { 1 }));
            });
        }

        [Test]
        public void audiobook_media_type_returns_only_audiobook_books_and_authors_with_audiobooks()
        {
            WithController(controller =>
            {
                var result = controller.Search("Winter", 10, "audiobook");

                Assert.That(result.Books, Has.Count.EqualTo(2));
                Assert.That(result.Books.SelectMany(book => book.LocalAudiobookBooks).Select(book => book.Id).OrderBy(id => id), Is.EqualTo(new[] { 10, 12 }));
                Assert.That(result.Books.SelectMany(book => book.LocalEbookBooks), Is.Empty);
                Assert.That(result.Authors.Select(author => author.Id).OrderBy(id => id), Is.EqualTo(new[] { 1, 2 }));
            });
        }

        [Test]
        public void postgres_search_filters_books_and_authors_by_media_type()
        {
            WithPostgresController(controller =>
            {
                var all = controller.Search("Winter", 10);
                var sharedWork = all.Books.Single(book => book.Id == 10);
                Assert.That(sharedWork.LocalAudiobookBooks.Select(book => book.Id), Is.EqualTo(new[] { 10 }));
                Assert.That(sharedWork.LocalEbookBooks.Select(book => book.Id), Is.EqualTo(new[] { 11 }));
                Assert.That(all.Authors.Select(author => author.Id).OrderBy(id => id), Is.EqualTo(new[] { 1, 2 }));

                var ebooks = controller.Search("Winter", 10, "ebook");
                Assert.That(ebooks.Books, Has.Count.EqualTo(1));
                Assert.That(ebooks.Books[0].LocalEbookBooks.Select(book => book.Id), Is.EqualTo(new[] { 11 }));
                Assert.That(ebooks.Books[0].LocalAudiobookBooks, Is.Empty);
                Assert.That(ebooks.Authors.Select(author => author.Id), Is.EqualTo(new[] { 1 }));

                var audiobooks = controller.Search("Winter", 10, "audiobook");
                Assert.That(audiobooks.Books.SelectMany(book => book.LocalAudiobookBooks)
                    .Select(book => book.Id).OrderBy(id => id), Is.EqualTo(new[] { 10, 12 }));
                Assert.That(audiobooks.Books.SelectMany(book => book.LocalEbookBooks), Is.Empty);
                Assert.That(audiobooks.Authors.Select(author => author.Id).OrderBy(id => id), Is.EqualTo(new[] { 1, 2 }));
            });
        }

        private static void WithController(Action<LibrarySearchController> action)
        {
            var databasePath = Path.Combine(TestContext.CurrentContext.WorkDirectory, $"library_search_{Guid.NewGuid():N}.db");
            var connectionString = new SqliteConnectionStringBuilder
            {
                DataSource = databasePath,
                Mode = SqliteOpenMode.ReadWriteCreate
            }.ToString();

            try
            {
                using (var connection = new SqliteConnection(connectionString))
                {
                    connection.Open();
                    CreateSchema<Author>(connection);
                    CreateSchema<Book>(connection);
                    CreateSchema<Edition>(connection);
                    connection.Execute("CREATE TABLE BookFiles (EditionId INTEGER NOT NULL);");
                    connection.Execute("CREATE VIRTUAL TABLE author_fts USING fts5(Name, SortName, TitleSlug);");
                    connection.Execute("CREATE VIRTUAL TABLE edition_fts USING fts5(MatchingTitle);");

                    connection.Execute(@"
INSERT INTO Authors (Id, Name, SortName, TitleSlug) VALUES
    (1, 'Winter Shared Author', 'Winter Shared Author', 'winter-shared-author'),
    (2, 'Winter Audio Author', 'Winter Audio Author', 'winter-audio-author');
INSERT INTO author_fts (rowid, Name, SortName, TitleSlug) VALUES
    (1, 'Winter Shared Author', 'Winter Shared Author', 'winter-shared-author'),
    (2, 'Winter Audio Author', 'Winter Audio Author', 'winter-audio-author');
INSERT INTO Books (Id, AuthorId, Title, TitleSlug, MediaType, AudiobookMonitored, EbookMonitored, BaseBookId, Narrator) VALUES
    (10, 1, 'Winter Tale', 'winter-tale-audio', 0, 1, 1, 'shared-work', 'Narrator'),
    (11, 1, 'Winter Tale', 'winter-tale-ebook', 1, 1, 1, 'shared-work', NULL),
    (12, 2, 'Winter Song', 'winter-song-audio', 0, 1, 1, 'audio-work', 'Narrator');
INSERT INTO Editions (Id, BookId, Title) VALUES
    (100, 10, 'Winter Tale Audio Edition'),
    (101, 11, 'Winter Tale Ebook Edition'),
    (102, 12, 'Winter Song Audio Edition');
INSERT INTO edition_fts (rowid, MatchingTitle) VALUES
    (100, 'Winter Tale Audio Edition'),
    (101, 'Winter Tale Ebook Edition'),
    (102, 'Winter Song Audio Edition');");
                }

                var database = new Database("main", () =>
                {
                    var connection = new SqliteConnection(connectionString);
                    connection.Open();
                    return connection;
                });
                var service = new LibrarySearchService(new MainDatabase(database), LogManager.GetLogger(nameof(LibrarySearchMediaTypeFixture)));
                action(new LibrarySearchController(service, new NoOpCoverMapper()));
            }
            finally
            {
                foreach (var suffix in new[] { "", "-wal", "-shm", "-journal" })
                {
                    var path = databasePath + suffix;
                    if (File.Exists(path))
                    {
                        File.Delete(path);
                    }
                }
            }
        }

        private static void WithPostgresController(Action<LibrarySearchController> action)
        {
            var baseConnectionString = Environment.GetEnvironmentVariable("CHAPTARRNG_POSTGRES_TEST_CONNECTION");
            if (string.IsNullOrWhiteSpace(baseConnectionString))
            {
                Assert.Ignore("Set CHAPTARRNG_POSTGRES_TEST_CONNECTION to exercise PostgreSQL library search filtering.");
            }

            var schema = "library_search_" + Guid.NewGuid().ToString("N");
            var adminConnectionString = new NpgsqlConnectionStringBuilder(baseConnectionString)
            {
                Pooling = false
            }.ConnectionString;
            var scopedConnectionString = new NpgsqlConnectionStringBuilder(baseConnectionString)
            {
                Pooling = false,
                SearchPath = schema
            }.ConnectionString;

            using var admin = new NpgsqlConnection(adminConnectionString);
            admin.Open();
            admin.Execute("CREATE SCHEMA \"" + schema + "\"");
            var succeeded = false;

            try
            {
                using (var connection = new NpgsqlConnection(scopedConnectionString))
                {
                    connection.Open();
                    connection.Execute(@"
CREATE TABLE ""Authors"" (
    ""Id"" INTEGER PRIMARY KEY,
    ""Name"" TEXT,
    ""SortName"" TEXT,
    ""TitleSlug"" TEXT,
    ""Images"" TEXT,
    ""SelectedPosterHash"" TEXT,
    ""HardcoverAuthorId"" TEXT,
    ""GoodreadsAuthorId"" TEXT,
    ""OpenLibraryAuthorId"" TEXT,
    ""GoogleBooksAuthorId"" TEXT,
    ""AudnexusAuthorId"" TEXT,
    ""RanobeDbAuthorId"" TEXT
);
CREATE TABLE ""Books"" (
    ""Id"" INTEGER PRIMARY KEY,
    ""AuthorId"" INTEGER,
    ""Title"" TEXT,
    ""TitleSlug"" TEXT,
    ""MediaType"" INTEGER,
    ""AudiobookMonitored"" BOOLEAN,
    ""EbookMonitored"" BOOLEAN,
    ""Images"" TEXT,
    ""BaseBookId"" TEXT,
    ""HardcoverBookId"" TEXT,
    ""GoodreadsBookId"" TEXT,
    ""GoodreadsWorkId"" TEXT,
    ""OpenLibraryWorkId"" TEXT,
    ""GoogleBooksId"" TEXT,
    ""ASIN"" TEXT,
    ""AudibleASIN"" TEXT,
    ""RanobeDbBookId"" TEXT,
    ""Narrator"" TEXT
);
CREATE TABLE ""Editions"" (""Id"" INTEGER PRIMARY KEY, ""BookId"" INTEGER);
CREATE TABLE ""BookFiles"" (""Id"" INTEGER PRIMARY KEY, ""EditionId"" INTEGER);
INSERT INTO ""Authors"" (""Id"", ""Name"", ""SortName"", ""TitleSlug"") VALUES
    (1, 'Winter Shared Author', 'Winter Shared Author', 'winter-shared-author'),
    (2, 'Winter Audio Author', 'Winter Audio Author', 'winter-audio-author');
INSERT INTO ""Books"" (""Id"", ""AuthorId"", ""Title"", ""TitleSlug"", ""MediaType"", ""AudiobookMonitored"", ""EbookMonitored"", ""BaseBookId"", ""Narrator"") VALUES
    (10, 1, 'Winter Tale', 'winter-tale-audio', 0, true, true, 'shared-work', 'Narrator'),
    (11, 1, 'Winter Tale', 'winter-tale-ebook', 1, true, true, 'shared-work', NULL),
    (12, 2, 'Winter Song', 'winter-song-audio', 0, true, true, 'audio-work', 'Narrator');");
                }

                var database = new Database("main", () =>
                {
                    var connection = new NpgsqlConnection(scopedConnectionString);
                    connection.Open();
                    return connection;
                });
                var service = new LibrarySearchService(new MainDatabase(database), LogManager.GetLogger(nameof(LibrarySearchMediaTypeFixture)));
                action(new LibrarySearchController(service, new NoOpCoverMapper()));
                succeeded = true;
            }
            finally
            {
                if (succeeded)
                {
                    admin.Execute("DROP SCHEMA \"" + schema + "\" CASCADE");
                }
                else
                {
                    TestContext.Progress.WriteLine("Retained failed synthetic PostgreSQL library search schema: " + schema);
                }
            }
        }

        private static void CreateSchema<T>(SqliteConnection connection)
            where T : ModelBase
        {
            var excluded = TableMapping.Mapper.ExcludeProperties(typeof(T))
                .Select(property => property.Name)
                .ToHashSet(StringComparer.OrdinalIgnoreCase);
            var tableName = TableMapping.Mapper.TableNameMapping(typeof(T));
            var columns = typeof(T)
                .GetProperties()
                .Where(property => property.Name == nameof(ModelBase.Id) || (property.IsMappableProperty() && !excluded.Contains(property.Name)))
                .GroupBy(property => property.Name, StringComparer.OrdinalIgnoreCase)
                .Select(group => group.First())
                .Select(property => property.Name == nameof(ModelBase.Id)
                    ? "\"Id\" INTEGER PRIMARY KEY AUTOINCREMENT"
                    : $"\"{property.Name}\" {GetSqliteColumnType(property)} NULL")
                .ToList();

            connection.Execute($"CREATE TABLE \"{tableName}\" ({string.Join(", ", columns)});");
        }

        private static string GetSqliteColumnType(System.Reflection.PropertyInfo property)
        {
            var type = Nullable.GetUnderlyingType(property.PropertyType) ?? property.PropertyType;
            return type.IsEnum || type == typeof(int) || type == typeof(long) || type == typeof(bool)
                ? "INTEGER"
                : "TEXT";
        }
    }
}

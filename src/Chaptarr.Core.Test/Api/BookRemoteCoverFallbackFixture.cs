using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Chaptarr.Api.V1.Books;
using NUnit.Framework;
using NzbDrone.Core.Books;
using NzbDrone.Core.MediaCover;
using NzbDrone.Core.MetadataSource;

namespace Chaptarr.Core.Test.Api
{
    [TestFixture]
    public class BookRemoteCoverFallbackFixture
    {
        private sealed class CoverMapperStub : IMapCoversToLocal
        {
            public void ConvertToLocalUrls(int entityId, MediaCoverEntity coverEntity, IEnumerable<NzbDrone.Core.MediaCover.MediaCover> covers, string selectedAuthorImageHash = null)
            {
            }

            public string GetCoverPath(int entityId, MediaCoverEntity coverEntity, MediaCoverTypes coverType, string extension, int? height = null) => throw new NotImplementedException();
            public void EnsureAuthorCovers(Author author) => throw new NotImplementedException();
            public void EnsureBookCovers(Book book) => throw new NotImplementedException();
            public Task<EnsureImageResult> EnsureAuthorImage(Author author, NzbDrone.Core.MediaCover.MediaCover cover) => throw new NotImplementedException();
        }

        private sealed class MediaCoverProxyStub : IMediaCoverProxy
        {
            public string RegisterUrl(string url) => "/MediaCoverProxy/test/" + System.IO.Path.GetFileName(new Uri(url).AbsolutePath);

            public bool IsProxyUrl(string url) => false;

            public bool TryResolveProxyUrl(string url, out string resolved)
            {
                resolved = null;
                return false;
            }

            public void ProxyRemoteUrls(IEnumerable<NzbDrone.Core.MediaCover.MediaCover> covers)
            {
                foreach (var cover in covers ?? Enumerable.Empty<NzbDrone.Core.MediaCover.MediaCover>())
                {
                    cover.Url = RegisterUrl(cover.Url);
                }
            }

            public string GetUrl(string hash) => throw new NotImplementedException();
            public byte[] GetImage(string hash) => throw new NotImplementedException();
        }

        private sealed class SearchProxyStub : ISearchForNewBook
        {
            private readonly Book _book;

            public SearchProxyStub(Book book)
            {
                _book = book;
            }

            public List<Book> SearchForNewBook(string title, string author, bool getAllEditions = true, BookMediaType? mediaType = null) => new List<Book> { _book };
            public List<Book> SearchByIsbn(string isbn) => throw new NotImplementedException();
            public List<Book> SearchByAsin(string asin) => throw new NotImplementedException();
            public List<Book> SearchByGoodreadsBookId(int goodreadsId, bool getAllEditions) => throw new NotImplementedException();
        }

        private static Edition Edition(int id, bool monitored, bool ebook, string coverUrl = null)
        {
            return new Edition
            {
                Id = id,
                ForeignEditionId = "hc:edition:" + id,
                Title = "The Eye of the Bedlam Bride",
                Monitored = monitored,
                IsEbook = ebook,
                Images = coverUrl == null
                    ? new List<NzbDrone.Core.MediaCover.MediaCover>()
                    : new List<NzbDrone.Core.MediaCover.MediaCover> { new NzbDrone.Core.MediaCover.MediaCover(MediaCoverTypes.Cover, coverUrl) }
            };
        }

        private static Book Book(BookMediaType mediaType, params Edition[] editions)
        {
            return new Book
            {
                Id = 2273,
                Title = "The Eye of the Bedlam Bride",
                MediaType = mediaType,
                HardcoverBookId = "hc:818989",
                Author = new Author { Name = "Matt Dinniman", HardcoverAuthorId = "hc:241306" },
                Editions = editions.ToList()
            };
        }

        private static BookResource Library(Book book) => book.ToResource(BookResourceMappingOptions.Rich());

        private static BookResource Lookup(Book book)
        {
            var controller = new BookLookupController(
                searchProxy: new SearchProxyStub(book),
                coverMapper: new CoverMapperStub(),
                bookService: null,
                editionService: null,
                mediaFileService: null,
                mediaCoverProxy: new MediaCoverProxyStub(),
                providerAliasService: null);

            return controller.Search("bedlam bride").Value.Single();
        }

        private static bool HasCover(BookResource resource) =>
            resource.Images.Any(i => i.CoverType == MediaCoverTypes.Cover);

        [Test]
        public void library_book_offers_another_audiobook_editions_cover_only_as_remote_cover()
        {
            var resource = Library(Book(
                BookMediaType.Audiobook,
                Edition(1, monitored: true, ebook: false),
                Edition(2, monitored: false, ebook: true, "https://covers.example/ebook.jpg"),
                Edition(3, monitored: false, ebook: false, "https://covers.example/audio.jpg")));

            Assert.That(HasCover(resource), Is.False, "Images stay the monitored edition's own art.");
            Assert.That(resource.RemoteCover, Is.EqualTo("https://covers.example/audio.jpg"));
        }

        [Test]
        public void library_book_falls_back_to_the_other_format_when_its_own_format_has_no_cover()
        {
            var resource = Library(Book(
                BookMediaType.Audiobook,
                Edition(1, monitored: true, ebook: false),
                Edition(2, monitored: false, ebook: true, "https://covers.example/ebook.jpg")));

            Assert.That(resource.RemoteCover, Is.EqualTo("https://covers.example/ebook.jpg"));
        }

        [Test]
        public void library_book_with_its_own_cover_keeps_an_empty_remote_cover()
        {
            var resource = Library(Book(
                BookMediaType.Audiobook,
                Edition(1, monitored: true, ebook: false, "https://covers.example/monitored.jpg"),
                Edition(2, monitored: false, ebook: false, "https://covers.example/other.jpg")));

            Assert.That(resource.Images.Single(i => i.CoverType == MediaCoverTypes.Cover).Url, Is.EqualTo("https://covers.example/monitored.jpg"));
            Assert.That(resource.RemoteCover, Is.Empty);
        }

        [Test]
        public void a_stock_no_image_picture_counts_as_no_cover()
        {
            foreach (var placeholder in new[]
            {
                "https://m.media-amazon.com/images/I/01RmK+J4pJL.gif",
                "https://m.media-amazon.com/images/I/01RmK%2BJ4pJL.gif"
            })
            {
                var resource = Library(Book(
                    BookMediaType.Audiobook,
                    Edition(1, monitored: true, ebook: false, placeholder),
                    Edition(2, monitored: false, ebook: false, placeholder),
                    Edition(3, monitored: false, ebook: false, "https://covers.example/real.jpg")));

                Assert.That(resource.RemoteCover, Is.EqualTo("https://covers.example/real.jpg"), placeholder);
            }
        }

        [Test]
        public void proxied_or_local_edition_covers_are_not_offered()
        {
            var resource = Library(Book(
                BookMediaType.Audiobook,
                Edition(1, monitored: true, ebook: false),
                Edition(2, monitored: false, ebook: false, "/MediaCoverProxy/abc/cover.jpg")));

            Assert.That(resource.RemoteCover, Is.Empty);
        }

        [Test]
        public void lean_list_books_get_the_fallback_from_their_loaded_editions()
        {
            // List endpoints load only the monitored edition on the book itself.
            var monitored = Edition(1, monitored: true, ebook: false);
            var book = Book(BookMediaType.Audiobook, monitored);
            var allEditions = new List<Edition>
            {
                monitored,
                Edition(2, monitored: false, ebook: false, "https://covers.example/audio.jpg")
            };

            Assert.That(Library(book).RemoteCover, Is.Empty);
            Assert.That(BookResourceMapper.SelectFallbackRemoteCover(book, allEditions, legacy: false),
                Is.EqualTo("https://covers.example/audio.jpg"));
            Assert.That(BookResourceMapper.SelectFallbackRemoteCover(book, allEditions, legacy: true),
                Is.EqualTo("https://covers.example/audio.jpg"));
        }

        [Test]
        public void lookup_offers_another_editions_cover_as_remote_cover_without_changing_images()
        {
            var resource = Lookup(Book(
                BookMediaType.Audiobook,
                Edition(1, monitored: true, ebook: false),
                Edition(2, monitored: false, ebook: false, "https://covers.example/audio.jpg")));

            Assert.That(HasCover(resource), Is.False);
            Assert.That(resource.RemoteCover, Is.EqualTo("https://covers.example/audio.jpg"));
        }

        [Test]
        public void lookup_without_any_edition_cover_has_no_remote_cover()
        {
            var resource = Lookup(Book(
                BookMediaType.Audiobook,
                Edition(1, monitored: true, ebook: false),
                Edition(2, monitored: false, ebook: false)));

            Assert.That(HasCover(resource), Is.False);
            Assert.That(resource.RemoteCover, Is.Null.Or.Empty);
        }
    }
}

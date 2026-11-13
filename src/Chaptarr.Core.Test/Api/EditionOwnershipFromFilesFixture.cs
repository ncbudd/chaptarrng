using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Chaptarr.Api.V1.Books;
using Chaptarr.Api.V1.Series;
using Microsoft.AspNetCore.Mvc;
using Moq;
using NLog;
using NUnit.Framework;
using NzbDrone.Core.AuthorStats;
using NzbDrone.Core.Books;
using NzbDrone.Core.Datastore;
using NzbDrone.Core.MediaCover;
using NzbDrone.Core.MediaFiles;
using NzbDrone.Core.Messaging.Commands;
using NzbDrone.Core.Messaging.Events;
using NzbDrone.Core.Profiles.Metadata;
using NzbDrone.Core.Profiles.Qualities;
using NzbDrone.Core.RootFolders;
using NzbDrone.SignalR;

namespace Chaptarr.Core.Test.Api
{
    // The edition service never loads Edition.BookFiles, so ownership must come from the file
    // service. These fixtures deliberately leave Edition.BookFiles null.
    [TestFixture]
    public class EditionOwnershipFromFilesFixture
    {
        private static Edition Audio(int id, int bookId, params string[] narrators) => new Edition
        {
            Id = id,
            BookId = bookId,
            Title = "Vol " + bookId,
            IsEbook = false,
            NarratorNames = narrators.ToList(),
            ForeignEditionId = "hc:" + id
        };

        private static SeriesBookLink Link(int bookId, int position) => new SeriesBookLink
        {
            IsPrimary = true,
            SeriesPosition = position,
            Book = new LazyLoaded<Book>(new Book { Id = bookId, Title = "Vol " + bookId })
        };

        [Test]
        public void series_matrix_should_mark_owned_from_files_without_edition_bookfiles()
        {
            var series = new NzbDrone.Core.Books.Series
            {
                Id = 7,
                Title = "Test Series",
                PrimaryWorkCount = 3,
                LinkItems = new List<SeriesBookLink> { Link(1, 1), Link(2, 2), Link(3, 3) }
            };

            var seriesService = new Mock<ISeriesService>();
            seriesService.Setup(s => s.GetAllSeries()).Returns(new List<NzbDrone.Core.Books.Series> { series });

            var editions = new Mock<IEditionService>();
            editions.Setup(e => e.GetEditionsByBook(1)).Returns(new List<Edition> { Audio(10, 1, "Jim Dale"), Audio(11, 1, "Stephen Fry") });
            editions.Setup(e => e.GetEditionsByBook(2)).Returns(new List<Edition> { Audio(12, 2, "Jim Dale") });
            editions.Setup(e => e.GetEditionsByBook(3)).Returns(new List<Edition> { Audio(13, 3, "Stephen Fry") });

            // Multi-file audiobook: many BookFile rows for one edition must collapse to one owned volume.
            var files = Enumerable.Range(0, 37).Select(_ => new BookFile { EditionId = 10 }).ToList();
            var fileService = new Mock<IMediaFileService>();
            fileService.Setup(f => f.GetFilesByBooks(It.IsAny<List<int>>())).Returns(files);

            var controller = new SeriesController(seriesService.Object, null, null, null, editions.Object, null, fileService.Object, LogManager.GetCurrentClassLogger());

            var result = controller.GetNarratorMatrix("Test Series");

            var matrix = (result.Result as OkObjectResult)?.Value as SeriesNarratorMatrixResource;
            Assert.That(matrix, Is.Not.Null);
            var dale = matrix.Narrators.Single(n => n.Name == "Jim Dale");
            Assert.That(dale.OwnedBookIds, Is.EqualTo(new[] { 1 }));
            Assert.That(matrix.Narrators.Single(n => n.Name == "Stephen Fry").OwnedBookIds, Is.Empty);
            Assert.That(matrix.Books[0].Narrators.Single(n => n.EditionId == 10).Owned, Is.True);
            Assert.That(matrix.Books[0].Narrators.Single(n => n.EditionId == 11).Owned, Is.False);
            fileService.Verify(f => f.GetFilesByBooks(It.IsAny<List<int>>()), Times.Once());
        }

        [Test]
        public void matrix_builder_should_use_owned_edition_ids()
        {
            var volumes = new List<SeriesNarratorMatrixBuilder.Volume>
            {
                new SeriesNarratorMatrixBuilder.Volume(1, "Vol 1", 1, new List<Edition> { Audio(10, 1, "Jim Dale") }, new HashSet<int> { 10 }),
                new SeriesNarratorMatrixBuilder.Volume(2, "Vol 2", 2, new List<Edition> { Audio(12, 2, "Jim Dale") }, new HashSet<int> { 10 })
            };

            var matrix = SeriesNarratorMatrixBuilder.Build(7, "Series", volumes);

            Assert.That(matrix.Narrators.Single().OwnedBookIds, Is.EqualTo(new[] { 1 }));
        }

        [Test]
        public void should_merge_narrator_names_that_differ_only_in_whitespace()
        {
            var edition = Audio(1, 1, "Jim  Dale", "Jim Dale", " Jim\tDale ");

            Assert.That(EditionCatalogMapper.NarratorsOf(edition), Is.EqualTo(new[] { "Jim Dale" }));
        }

        [Test]
        public void bookshelf_edition_catalog_should_mark_owned_from_files_without_edition_bookfiles()
        {
            var editions = new Mock<IEditionService>();
            editions.Setup(e => e.GetEditionsByBook(It.IsAny<List<int>>())).Returns(new List<Edition> { Audio(10, 1, "Jim Dale"), Audio(11, 1, "Stephen Fry") });
            var fileService = new Mock<IMediaFileService>();
            fileService.Setup(f => f.GetFilesByBooks(It.IsAny<List<int>>())).Returns(new List<BookFile> { new BookFile { EditionId = 10 } });

            var controller = new BookController(
                null, new Mock<IBookService>().Object, null, editions.Object, null, null, null,
                fileService.Object, null, null, null, null, null, null, null, null, null, null, null,
                LogManager.GetCurrentClassLogger());

            var method = typeof(BookController).GetMethod("GetBookshelfEditionCatalog", BindingFlags.NonPublic | BindingFlags.Instance);
            var catalog = (List<EditionCatalogResource>)method.Invoke(controller, new object[] { new List<int> { 1 }, null });

            Assert.That(catalog.Single(c => c.EditionId == 10).Owned, Is.True);
            Assert.That(catalog.Single(c => c.EditionId == 11).Owned, Is.False);
        }
    }
}

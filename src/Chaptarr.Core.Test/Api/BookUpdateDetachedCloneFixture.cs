using System.Collections.Generic;
using System.Linq;
using Chaptarr.Api.V1.Books;
using Newtonsoft.Json;
using NUnit.Framework;
using NzbDrone.Common.Extensions;
using NzbDrone.Core.Books;
using NzbDrone.Core.MediaFiles;

namespace Chaptarr.Core.Test.Api
{
    // PUT /api/v1/book/{id} copies the stored book before applying the submitted selection.
    // BookService.GetBook loads editions through EditionRepository.FindByBook, which points
    // every edition back at a joined copy of the same book (Entity equality is by value), so
    // a plain JsonClone of that graph fails with "Self referencing loop detected ...
    // Path 'lazyEditions.value[0].lazyBook'" and every book update answered 500.
    [TestFixture]
    public class BookUpdateDetachedCloneFixture
    {
        private static Book StoredBookGraph()
        {
            var author = new NzbDrone.Core.Books.Author { Id = 7 };

            Book Row() => new Book
            {
                Id = 2805,
                Title = "Project Hail Mary",
                TitleSlug = "427578",
                MediaType = BookMediaType.Ebook,
                EbookMonitored = false,
                AnyEditionOk = true,
                HardcoverBookId = "427578",
                Author = author
            };

            var book = Row();
            var joined = Row();

            var first = new Edition
            {
                Id = 14908,
                BookId = 2805,
                ForeignEditionId = "hc:edition:30405492-ebook",
                HardcoverEditionId = "30405492",
                Title = "Project Hail Mary: A Novel",
                IsEbook = true,
                Monitored = true,
                Book = joined
            };
            var second = new Edition
            {
                Id = 14909,
                BookId = 2805,
                ForeignEditionId = "hc:edition:30436691-ebook",
                HardcoverEditionId = "30436691",
                Title = "Project Hail Mary",
                IsEbook = true,
                Monitored = false,
                Book = joined
            };
            first.BookFiles = new List<BookFile> { new BookFile { Id = 1, EditionId = 14908, Edition = first } };

            book.Editions = new List<Edition> { first, second };
            joined.Editions = book.Editions;
            return book;
        }

        [Test]
        public void plain_json_clone_of_a_stored_book_graph_loops()
        {
            Assert.Throws<JsonSerializationException>(() => StoredBookGraph().JsonClone());
        }

        [Test]
        public void detached_clone_copies_the_book_and_its_editions_without_the_back_references()
        {
            var stored = StoredBookGraph();

            var copy = DetachedEntityClone.Clone(stored);

            Assert.Multiple(() =>
            {
                Assert.That(copy, Is.Not.SameAs(stored));
                Assert.That(copy.Id, Is.EqualTo(2805));
                Assert.That(copy.AuthorId, Is.EqualTo(7));
                Assert.That(copy.Author, Is.SameAs(stored.Author));
                Assert.That(copy.AnyEditionOk, Is.True);
                Assert.That(copy.Editions.Select(e => e.Id), Is.EqualTo(new[] { 14908, 14909 }));
                Assert.That(copy.Editions[0], Is.Not.SameAs(stored.Editions[0]));
                Assert.That(copy.Editions[0].ForeignEditionId, Is.EqualTo("hc:edition:30405492-ebook"));
                Assert.That(copy.Editions[0].Monitored, Is.True);
                Assert.That(copy.Editions[0].BookId, Is.EqualTo(2805));
                Assert.That(copy.Editions[0].LazyBook, Is.Null);
            });

            copy.Editions[0].Monitored = false;
            Assert.That(stored.Editions[0].Monitored, Is.True, "the copy must not write through to the stored rows");
        }

        [Test]
        public void put_selection_maps_onto_stored_editions_of_a_loaded_graph()
        {
            var stored = StoredBookGraph();
            var resource = new BookResource
            {
                Id = 2805,
                Monitored = true,
                Editions = new List<EditionResource>
                {
                    new EditionResource { Id = 14908, Monitored = false, ForeignEditionId = "30405492", Title = "client title" },
                    new EditionResource { Id = 14909, Monitored = true, ForeignEditionId = "30436691" }
                }
            };

            Book model = null;
            Assert.DoesNotThrow(() => model = resource.ToModel(DetachedEntityClone.Clone(stored), null));
            Assert.DoesNotThrow(() => resource.ToModel(StoredBookGraph(), null));

            Assert.Multiple(() =>
            {
                Assert.That(model.Editions.Select(e => e.Monitored), Is.EqualTo(new[] { false, true }));
                Assert.That(model.Editions[0].ForeignEditionId, Is.EqualTo("hc:edition:30405492-ebook"));
                Assert.That(model.Editions[0].Title, Is.EqualTo("Project Hail Mary: A Novel"));
            });
        }
    }
}

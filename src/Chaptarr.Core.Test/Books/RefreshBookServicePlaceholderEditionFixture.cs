using System.Collections.Generic;
using System.Reflection;
using NLog;
using NUnit.Framework;
using NzbDrone.Core.Books;
using NzbDrone.Core.MediaFiles;

namespace Chaptarr.Core.Test.Books
{
    [TestFixture]
    public class RefreshBookServicePlaceholderEditionFixture
    {
        private sealed class TestableRefreshBookService : RefreshBookService
        {
            public TestableRefreshBookService(Logger logger)
                : base(bookService: null,
                    authorService: null,
                    rootFolderService: null,
                    editionService: null,
                    authorInfo: null,
                    bookInfo: null,
                    refreshEditionService: null,
                    mediaFileService: null,
                    historyService: null,
                    eventAggregator: null,
                    checkIfBookShouldBeRefreshed: null,
                    editionSelector: new EditionSelector(logger),
                    editionMetadataProfileFilter: null,
                    mediaCoverService: null,
                    logger: logger)
            {
            }

            public void InvokeMonitor(List<Edition> existing, List<Edition> added)
            {
                var children = new SortedChildren
                {
                    UpToDate = existing,
                    Added = added
                };

                typeof(RefreshBookService)
                    .GetMethod("MonitorSingleEdition", BindingFlags.Instance | BindingFlags.NonPublic)
                    .Invoke(this, new object[] { children });
            }
        }

        private static Book NewBook()
        {
            return new Book
            {
                Id = 7,
                Title = "A Court of Thorns and Roses 6",
                SeriesName = "A Court of Thorns and Roses",
                SeriesPosition = "6",
                MediaType = BookMediaType.Audiobook,
                AnyEditionOk = false
            };
        }

        private static Edition NewEdition(Book book, int id, string foreignId, string title, bool monitored, bool manualAdd,
            int format = 2, string language = "eng", string narrator = "Jane Doe")
        {
            return new Edition
            {
                Id = id,
                BookId = book.Id,
                Book = book,
                ForeignEditionId = foreignId,
                Title = title,
                ReadingFormatId = format,
                Language = language,
                Narrator = narrator,
                Monitored = monitored,
                ManualAdd = manualAdd
            };
        }

        private static void Run(List<Edition> existing, List<Edition> added)
        {
            new TestableRefreshBookService(LogManager.GetCurrentClassLogger()).InvokeMonitor(existing, added);
        }

        [Test]
        public void should_move_pinned_placeholder_to_single_real_edition_of_same_format()
        {
            var book = NewBook();
            var placeholder = NewEdition(book, 10, "hc:edition:1-audiobook", "A Court of Thorns and Roses 6", true, true);
            var real = NewEdition(book, 0, "hc:edition:2-audiobook", "A Court of Silver Flames", false, false);
            var ebook = NewEdition(book, 0, "hc:edition:3-ebook", "A Court of Silver Flames", false, false, format: 3, narrator: null);

            Run(new List<Edition> { placeholder }, new List<Edition> { real, ebook });

            Assert.That(real.Monitored, Is.True);
            Assert.That(real.ManualAdd, Is.True, "the pin moves with monitoring");
            Assert.That(placeholder.Monitored, Is.False);
            Assert.That(placeholder.ManualAdd, Is.False);
            Assert.That(ebook.Monitored, Is.False);
            Assert.That(book.AnyEditionOk, Is.False);
        }

        [Test]
        public void should_match_placeholder_equal_to_series_name_and_position()
        {
            var book = NewBook();
            book.SeriesName = "ACOTAR";
            book.SeriesPosition = "6";
            var placeholder = NewEdition(book, 10, "hc:edition:1-audiobook", "ACOTAR #6", true, true);
            var real = NewEdition(book, 0, "hc:edition:2-audiobook", "A Court of Silver Flames", false, false);

            Run(new List<Edition> { placeholder }, new List<Edition> { real });

            Assert.That(real.Monitored, Is.True);
            Assert.That(placeholder.Monitored, Is.False);
        }

        [Test]
        public void should_keep_placeholder_when_several_real_candidates_exist()
        {
            var book = NewBook();
            var placeholder = NewEdition(book, 10, "hc:edition:1-audiobook", "A Court of Thorns and Roses 6", true, true);
            var realA = NewEdition(book, 0, "hc:edition:2-audiobook", "A Court of Silver Flames", false, false);
            var realB = NewEdition(book, 0, "hc:edition:4-audiobook", "A Court of Silver Flames (Unabridged)", false, false);

            Run(new List<Edition> { placeholder }, new List<Edition> { realA, realB });

            Assert.That(placeholder.Monitored, Is.True);
            Assert.That(placeholder.ManualAdd, Is.True);
            Assert.That(realA.Monitored, Is.False);
            Assert.That(realB.Monitored, Is.False);
        }

        [Test]
        public void should_keep_pinned_edition_that_is_not_a_placeholder()
        {
            var book = NewBook();
            var pinned = NewEdition(book, 10, "hc:edition:1-audiobook", "A Court of Silver Flames (Dramatized)", true, true);
            var real = NewEdition(book, 0, "hc:edition:2-audiobook", "A Court of Silver Flames", false, false);

            Run(new List<Edition> { pinned }, new List<Edition> { real });

            Assert.That(pinned.Monitored, Is.True);
            Assert.That(pinned.ManualAdd, Is.True);
            Assert.That(real.Monitored, Is.False);
        }

        [Test]
        public void should_keep_placeholder_when_book_has_files()
        {
            var book = NewBook();
            var placeholder = NewEdition(book, 10, "hc:edition:1-audiobook", "A Court of Thorns and Roses 6", true, true);
            placeholder.BookFiles = new List<BookFile> { new BookFile { Id = 1, EditionId = 10 } };
            var real = NewEdition(book, 0, "hc:edition:2-audiobook", "A Court of Silver Flames", false, false);

            Run(new List<Edition> { placeholder }, new List<Edition> { real });

            Assert.That(placeholder.Monitored, Is.True);
            Assert.That(real.Monitored, Is.False);
        }

        [Test]
        public void should_keep_audiobook_placeholder_when_narrator_differs()
        {
            var book = NewBook();
            var placeholder = NewEdition(book, 10, "hc:edition:1-audiobook", "A Court of Thorns and Roses 6", true, true, narrator: "Jane Doe");
            var real = NewEdition(book, 0, "hc:edition:2-audiobook", "A Court of Silver Flames", false, false, narrator: "John Roe");

            Run(new List<Edition> { placeholder }, new List<Edition> { real });

            Assert.That(placeholder.Monitored, Is.True);
            Assert.That(real.Monitored, Is.False);
        }

        [Test]
        public void should_keep_placeholder_when_language_differs()
        {
            var book = NewBook();
            var placeholder = NewEdition(book, 10, "hc:edition:1-audiobook", "A Court of Thorns and Roses 6", true, true, language: "eng");
            var real = NewEdition(book, 0, "hc:edition:2-audiobook", "Ein Hof aus Silber und Flammen", false, false, language: "ger");

            Run(new List<Edition> { placeholder }, new List<Edition> { real });

            Assert.That(placeholder.Monitored, Is.True);
            Assert.That(real.Monitored, Is.False);
        }

        [Test]
        public void should_not_treat_title_with_unrelated_number_as_placeholder()
        {
            var book = NewBook();
            var pinned = NewEdition(book, 10, "hc:edition:1-audiobook", "Fahrenheit 11", true, true);
            var real = NewEdition(book, 0, "hc:edition:2-audiobook", "A Court of Silver Flames", false, false);

            Run(new List<Edition> { pinned }, new List<Edition> { real });

            Assert.That(pinned.Monitored, Is.True);
            Assert.That(real.Monitored, Is.False);
        }
    }
}

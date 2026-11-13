using System.Collections.Generic;
using NUnit.Framework;
using NzbDrone.Core.Books;
using NzbDrone.Core.MediaFiles;
using NzbDrone.Core.Parser.Model;

namespace Chaptarr.Core.Test.MediaFiles
{
    [TestFixture]
    public class TrackedDownloadSameRecordingFixture
    {
        private static Edition Audiobook(int id, string language, params string[] narrators)
        {
            return new Edition
            {
                Id = id,
                Title = "Project Hail Mary",
                Language = language,
                IsEbook = false,
                ReadingFormatId = 2,
                NarratorNames = new List<string>(narrators)
            };
        }

        [Test]
        public void should_accept_another_listing_of_the_same_narration()
        {
            // Hardcover and Audible list the Ray Porter recording separately
            var grabbed = Audiobook(1, "eng", "Ray Porter");
            var matched = Audiobook(2, "en", "Ray  Porter");

            Assert.That(DownloadedBooksImportService.IsSameRecording(grabbed, matched), Is.True);
        }

        [Test]
        public void should_reject_a_different_narrator()
        {
            Assert.That(DownloadedBooksImportService.IsSameRecording(Audiobook(1, "eng", "Jim Dale"), Audiobook(2, "eng", "Stephen Fry")), Is.False);
        }

        [Test]
        public void should_reject_another_language()
        {
            Assert.That(DownloadedBooksImportService.IsSameRecording(Audiobook(1, "eng", "Ray Porter"), Audiobook(2, "ita", "Ray Porter")), Is.False);
        }

        [Test]
        public void should_reject_when_language_is_unknown()
        {
            Assert.That(DownloadedBooksImportService.IsSameRecording(Audiobook(1, null, "Ray Porter"), Audiobook(2, null, "Ray Porter")), Is.False);
            Assert.That(DownloadedBooksImportService.IsSameRecording(Audiobook(1, "eng", "Ray Porter"), Audiobook(2, null, "Ray Porter")), Is.False);
        }

        [Test]
        public void should_not_judge_editions_without_narrators_or_with_a_full_cast_label()
        {
            Assert.That(DownloadedBooksImportService.IsSameRecording(Audiobook(1, "eng"), Audiobook(2, "eng")), Is.False);
            Assert.That(DownloadedBooksImportService.IsSameRecording(Audiobook(1, "eng", "Full Cast"), Audiobook(2, "eng", "Full Cast")), Is.False);
        }

        [Test]
        public void should_not_apply_to_ebooks()
        {
            var grabbed = new Edition { Id = 1, IsEbook = true, Language = "eng", NarratorNames = new List<string> { "Ray Porter" } };
            var matched = new Edition { Id = 2, IsEbook = true, Language = "eng", NarratorNames = new List<string> { "Ray Porter" } };

            Assert.That(DownloadedBooksImportService.IsSameRecording(grabbed, matched), Is.False);
        }

        [TestCase("Project Hail Mary: A Novel", "Project Hail Mary", true)]
        [TestCase("Project Hail Mary", "Project Hail Mary: A Novel", true)]
        [TestCase("Project Hail Mary: A Novel", "Project Hail Mary", true)]
        [TestCase("Pride and Prejudice", "Pride and Prejudice and Kitties", false)]
        [TestCase("Project Hail Mary: Illustrated Edition", "Project Hail Mary", false)]
        public void should_only_accept_equivalent_ebook_titles(string grabbedTitle, string matchedTitle, bool accepted)
        {
            var grabbed = new Edition { Id = 1, IsEbook = true, Language = "eng", Title = grabbedTitle };
            var matched = new Edition { Id = 2, IsEbook = true, Language = "eng", Title = matchedTitle };

            Assert.That(DownloadedBooksImportService.IsEquivalentEbookTitle(grabbed, matched), Is.EqualTo(accepted));
            matched.IsEbook = false;
            Assert.That(DownloadedBooksImportService.IsEquivalentEbookTitle(grabbed, matched), Is.False);
        }

        [Test]
        public void should_reject_equivalent_ebook_titles_with_conflicting_or_unknown_languages()
        {
            var grabbed = new Edition { Id = 1, IsEbook = true, Language = "eng", Title = "Project Hail Mary: A Novel" };
            var matched = new Edition { Id = 2, IsEbook = true, Language = "deu", Title = "Project Hail Mary" };

            Assert.That(DownloadedBooksImportService.IsEquivalentEbookTitle(grabbed, matched), Is.False);

            matched.Language = null;
            Assert.That(DownloadedBooksImportService.IsEquivalentEbookTitle(grabbed, matched), Is.False);
        }

        [Test]
        public void should_match_file_isbn_to_the_exact_pinned_edition()
        {
            var localBook = new LocalBook
            {
                RawTags = new RawFileTags
                {
                    AllTags = new Dictionary<string, List<string>>
                    {
                        ["ISBN-10"] = new List<string> { "0-306-40615-2" }
                    }
                }
            };
            var expected = new Edition { Isbn13 = "9780306406157", Isbn10 = "0306406152" };

            Assert.That(DownloadedBooksImportService.HasExactExpectedEditionIsbn(localBook, expected), Is.True);
            Assert.That(DownloadedBooksImportService.HasExactExpectedEditionIsbn(localBook, new Edition { Isbn13 = "9783161484100" }), Is.False);
        }

        [Test]
        public void should_retarget_an_isbn_match_only_within_the_matched_book()
        {
            var book = new Book { Id = 4 };
            var matchedEdition = new Edition { Id = 9, BookId = book.Id, IsEbook = true };
            var expectedEdition = new Edition { Id = 10, BookId = book.Id, IsEbook = true };
            var localBook = new LocalBook { Book = book, Edition = matchedEdition };

            Assert.That(DownloadedBooksImportService.TryRetargetToExpectedEdition(localBook, book, expectedEdition), Is.True);
            Assert.That(localBook.Edition, Is.SameAs(expectedEdition));

            var otherBookEdition = new Edition { Id = 11, BookId = book.Id + 1, IsEbook = true };
            Assert.That(DownloadedBooksImportService.TryRetargetToExpectedEdition(localBook, book, otherBookEdition), Is.False);
            Assert.That(localBook.Edition, Is.SameAs(expectedEdition));

            var audiobookEdition = Audiobook(12, "eng", "Ray Porter");
            audiobookEdition.BookId = book.Id;
            Assert.That(DownloadedBooksImportService.TryRetargetToExpectedEdition(localBook, book, audiobookEdition), Is.False);
            Assert.That(localBook.Edition, Is.SameAs(expectedEdition));

            var matchedAudiobook = Audiobook(13, "eng", "Ray Porter");
            var expectedAudiobook = Audiobook(14, "eng", "Ray Porter");
            matchedAudiobook.BookId = book.Id;
            expectedAudiobook.BookId = book.Id;
            var audiobookLocalBook = new LocalBook { Book = book, Edition = matchedAudiobook };
            Assert.That(DownloadedBooksImportService.TryRetargetToExpectedEdition(audiobookLocalBook, book, expectedAudiobook), Is.True);
            Assert.That(audiobookLocalBook.Edition, Is.SameAs(expectedAudiobook));
        }
    }
}

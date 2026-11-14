using System.Collections.Generic;
using NLog;
using NUnit.Framework;
using NzbDrone.Core.Books;
using NzbDrone.Core.DecisionEngine.Specifications;
using NzbDrone.Core.IndexerSearch.Definitions;
using NzbDrone.Core.Parser.Model;
using NzbDrone.Core.Qualities;

namespace Chaptarr.Core.Test.DecisionEngine
{
    [TestFixture]
    public class PinnedNarratorSpecificationFixture
    {
        private static PinnedNarratorSpecification CreateSubject()
        {
            return new PinnedNarratorSpecification(LogManager.GetCurrentClassLogger());
        }

        [Test]
        public void should_reject_when_release_narrator_differs_from_pinned_narrator()
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: "Michael Kramer");

            var decision = CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria());

            Assert.That(decision.Accepted, Is.False);
            Assert.That(decision.CanBypass, Is.True);
            Assert.That(decision.Category, Is.EqualTo("Narrator"));
            Assert.That(decision.Reason, Does.Contain("Michael Kramer"));
            Assert.That(decision.Reason, Does.Contain("Roy Dotrice"));
        }

        [Test]
        public void should_reject_when_title_labels_a_different_narrator()
        {
            var remoteBook = BuildRemoteBook(title: "Some Book - Narrated by Michael Kramer - M4B");

            var decision = CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria());

            Assert.That(decision.Accepted, Is.False);
        }

        [Test]
        public void should_accept_when_release_narrator_matches_pinned_narrator()
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: "Roy Dotrice");

            Assert.That(CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria()).Accepted, Is.True);
        }

        [Test]
        public void should_accept_when_release_narrator_is_unknown()
        {
            var remoteBook = BuildRemoteBook();

            Assert.That(CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria()).Accepted, Is.True);
        }

        [Test]
        public void should_accept_ebook_release()
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: "Michael Kramer", quality: Quality.EPUB);

            Assert.That(CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria()).Accepted, Is.True);
        }

        [Test]
        public void should_accept_when_any_edition_is_ok()
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: "Michael Kramer", anyEditionOk: true);

            Assert.That(CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria()).Accepted, Is.True);
        }

        [Test]
        public void should_accept_when_multiple_editions_are_monitored()
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: "Michael Kramer", secondMonitoredEdition: true);

            Assert.That(CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria()).Accepted, Is.True);
        }

        [Test]
        public void should_reject_a_multi_book_release_when_one_pinned_book_narrator_mismatches()
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: "Roy Dotrice", secondPinnedBook: true);

            var decision = CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria());

            Assert.That(decision.Accepted, Is.False);
            Assert.That(decision.Category, Is.EqualTo("Narrator"));
        }

        [Test]
        public void should_accept_a_multi_book_release_when_each_pinned_book_narrator_matches()
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: "Roy Dotrice, Michael Kramer", secondPinnedBook: true);

            Assert.That(CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria()).Accepted, Is.True);
        }

        [Test]
        public void should_reject_when_release_lists_only_some_narrators_from_the_pinned_edition()
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: "Roy Dotrice");
            remoteBook.Books[0].Editions[0].Narrator = "Roy Dotrice, Neil Gaiman";
            remoteBook.Books[0].Editions[0].NarratorNames = new List<string> { "Roy Dotrice", "Neil Gaiman" };

            Assert.That(CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria()).Accepted, Is.False);
        }

        [Test]
        public void should_reject_when_release_lists_an_unpinned_extra_narrator()
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: "Roy Dotrice, Michael Kramer");

            Assert.That(CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria()).Accepted, Is.False);
        }

        [Test]
        public void should_accept_when_release_lists_all_narrators_from_the_pinned_edition()
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: "Roy Dotrice, Neil Gaiman");
            remoteBook.Books[0].Editions[0].Narrator = "Roy Dotrice, Neil Gaiman";
            remoteBook.Books[0].Editions[0].NarratorNames = new List<string> { "Roy Dotrice", "Neil Gaiman" };

            Assert.That(CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria()).Accepted, Is.True);
        }

        [Test]
        public void should_use_the_unambiguous_book_media_type_when_parsed_quality_is_missing()
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: "Michael Kramer");
            remoteBook.Release.Title = "Some Book";
            remoteBook.ParsedBookInfo.BookTitle = "Some Book Identified";
            remoteBook.ParsedBookInfo.Quality = null;

            var decision = CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria());

            Assert.That(decision.Accepted, Is.False);
        }

        [Test]
        public void should_not_use_search_criteria_when_resolved_books_have_mixed_media_types()
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: "Michael Kramer");
            remoteBook.Release.Title = "Some Book";
            remoteBook.ParsedBookInfo.BookTitle = "Some Book Identified";
            remoteBook.ParsedBookInfo.Quality = null;
            remoteBook.Books.Add(new Book { Id = 2, MediaType = BookMediaType.Ebook, AnyEditionOk = true });
            var criteria = new BookSearchCriteria
            {
                Books = new List<Book> { new Book { Id = 3, MediaType = BookMediaType.Audiobook } }
            };

            Assert.That(CreateSubject().IsSatisfiedBy(remoteBook, criteria).Accepted, Is.True);
        }

        [TestCase("Various")]
        [TestCase("Unknown")]
        [TestCase("Full Cast")]
        public void should_allow_generic_release_narrator_labels(string narrator)
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: narrator);

            Assert.That(CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria()).Accepted, Is.True);
        }

        [Test]
        public void should_use_specific_parsed_narrator_when_release_metadata_is_generic()
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: "Various");
            remoteBook.ParsedBookInfo.Narrator = "Michael Kramer";

            var decision = CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria());

            Assert.That(decision.Accepted, Is.False);
        }

        [Test]
        public void should_not_treat_a_generic_edition_narrator_as_a_pinned_target()
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: "Michael Kramer");
            remoteBook.Books[0].Editions[0].Narrator = "Various";
            remoteBook.Books[0].Editions[0].NarratorNames = new List<string> { "Various" };

            Assert.That(CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria()).Accepted, Is.True);
        }

        [Test]
        public void should_honor_a_manually_selected_audiobook_edition_even_when_any_edition_is_allowed()
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: "Michael Kramer");
            remoteBook.Books[0].AnyEditionOk = true;
            remoteBook.Books[0].Editions[0].ManualAdd = true;

            var decision = CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria());

            Assert.That(decision.Accepted, Is.False);
        }

        [Test]
        public void should_escape_provider_control_characters_in_narrator_rejection_details()
        {
            var remoteBook = BuildRemoteBook(releaseNarrator: "Michael Kramer\r\nWARN: forged entry");

            var decision = CreateSubject().IsSatisfiedBy(remoteBook, new BookSearchCriteria());

            Assert.That(decision.Accepted, Is.False);
            Assert.That(decision.Reason, Does.Not.Contain("\r"));
            Assert.That(decision.Reason, Does.Not.Contain("\n"));
        }

        private static RemoteBook BuildRemoteBook(string title = "Some Book M4B", string releaseNarrator = null, Quality quality = null, bool anyEditionOk = false, bool secondMonitoredEdition = false, bool secondPinnedBook = false)
        {
            var editions = new List<Edition>
            {
                new Edition
                {
                    Id = 1,
                    Title = "Some Book",
                    Monitored = true,
                    IsEbook = false,
                    Narrator = "Roy Dotrice",
                    NarratorNames = new List<string> { "Roy Dotrice" }
                }
            };

            if (secondMonitoredEdition)
            {
                editions.Add(new Edition
                {
                    Id = 2,
                    Title = "Some Book",
                    Monitored = true,
                    IsEbook = false,
                    Narrator = "Michael Kramer",
                    NarratorNames = new List<string> { "Michael Kramer" }
                });
            }

            var book = new Book
            {
                Title = "Some Book",
                MediaType = BookMediaType.Audiobook,
                AnyEditionOk = anyEditionOk,
                Editions = editions
            };

            var books = new List<Book> { book };
            if (secondPinnedBook)
            {
                books.Add(new Book
                {
                    Id = 2,
                    Title = "Another Book",
                    MediaType = BookMediaType.Audiobook,
                    Editions = new List<Edition>
                    {
                        new Edition
                        {
                            Id = 3,
                            Title = "Another Book",
                            Monitored = true,
                            IsEbook = false,
                            Narrator = "Michael Kramer",
                            NarratorNames = new List<string> { "Michael Kramer" }
                        }
                    }
                });
            }

            return new RemoteBook
            {
                Author = new Author { Name = "Jane Doe" },
                Books = books,
                ParsedBookInfo = new ParsedBookInfo
                {
                    AuthorName = "Jane Doe",
                    BookTitle = "Some Book",
                    Quality = new QualityModel(quality ?? Quality.M4B)
                },
                Release = new ReleaseInfo
                {
                    Title = title,
                    Author = "Jane Doe",
                    Narrator = releaseNarrator
                }
            };
        }
    }
}

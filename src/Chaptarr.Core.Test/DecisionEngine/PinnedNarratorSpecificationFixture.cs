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

        private static RemoteBook BuildRemoteBook(string title = "Some Book M4B", string releaseNarrator = null, Quality quality = null, bool anyEditionOk = false, bool secondMonitoredEdition = false)
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

            return new RemoteBook
            {
                Author = new Author { Name = "Jane Doe" },
                Books = new List<Book> { book },
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

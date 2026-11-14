using System.Collections.Generic;
using System.Linq;
using NLog;
using NzbDrone.Core.Books;
using NzbDrone.Core.CustomFormats;
using NzbDrone.Common.Instrumentation;
using NzbDrone.Core.IndexerSearch.Definitions;
using NzbDrone.Core.Parser.Model;
using NzbDrone.Core.Qualities;

namespace NzbDrone.Core.DecisionEngine.Specifications
{
    /// <summary>
    /// Rejects an audiobook release whose narrator is known and differs from the narrator(s) of the
    /// edition the request is pinned to. A release that names no narrator is still allowed, because
    /// many indexers (usenet, MyAnonamouse) never put the narrator in the title; those releases keep
    /// being ranked by the narrator custom formats. The rejection can be bypassed from a manual search.
    /// </summary>
    public class PinnedNarratorSpecification : IDecisionEngineSpecification
    {
        private static readonly HashSet<string> GenericNarratorNames = new HashSet<string>(System.StringComparer.OrdinalIgnoreCase)
        {
            "various",
            "various artists",
            "various narrators",
            "unknown",
            "unknown narrator",
            "uncredited",
            "full cast",
            "multiple narrators",
            "multiple performers",
            "various voices",
            "not stated",
            "not available",
            "no narrator",
            "none",
            "n/a"
        };

        private readonly Logger _logger;

        public PinnedNarratorSpecification(Logger logger)
        {
            _logger = logger;
        }

        public SpecificationPriority Priority => SpecificationPriority.Default;
        public RejectionType Type => RejectionType.Permanent;

        public Decision IsSatisfiedBy(RemoteBook subject, SearchCriteriaBase searchCriteria)
        {
            var release = subject?.Release;
            var books = subject?.Books;

            if (release == null || books == null || books.Count == 0)
            {
                return Decision.Accept();
            }

            if (ResolveMediaType(subject, searchCriteria) != BookMediaType.Audiobook)
            {
                return Decision.Accept();
            }

            var targets = new List<List<string>>();
            foreach (var book in books)
            {
                var target = GetPinnedTarget(book);
                if (target != null)
                {
                    targets.Add(target);
                }
            }

            if (targets.Count == 0)
            {
                return Decision.Accept();
            }

            var releaseNarrators = GetExplicitReleaseNarrators(subject);
            if (releaseNarrators.Count == 0)
            {
                _logger.Trace("[PINNED_NARRATOR] No specific narrator found in release metadata, allowing");
                return Decision.Accept();
            }

            var pinnedNarrators = targets.SelectMany(target => target).Distinct(System.StringComparer.OrdinalIgnoreCase).ToList();
            var everyPinnedNarratorMatches = pinnedNarrators.All(name =>
                releaseNarrators.Any(narrator => PreferredNarratorMatcher.IsNarratorNameMatch(narrator, name)));
            var everyReleaseNarratorMatches = releaseNarrators.All(narrator =>
                pinnedNarrators.Any(name => PreferredNarratorMatcher.IsNarratorNameMatch(narrator, name)));
            if (everyPinnedNarratorMatches && everyReleaseNarratorMatches)
            {
                return Decision.Accept();
            }

            var wanted = CleanseLogMessage.Cleanse(string.Join(", ", targets.SelectMany(t => t).Distinct()));
            return Decision.RejectSoftFilter(
                "Release narrator [{0}] does not match the pinned narrator [{1}]",
                "Narrator",
                CleanseLogMessage.Cleanse(string.Join(", ", releaseNarrators)),
                wanted);
        }

        private static List<string> GetPinnedTarget(Book book)
        {
            if (book == null)
            {
                return null;
            }

            var protectedEditions = EditionPinPolicy.GetProtectedEditions(book, book.Editions)
                .Where(PreferredNarratorMatcher.IsAudiobookEdition)
                .ToList();

            if (protectedEditions.Count != 1)
            {
                return null;
            }

            var target = PreferredNarratorMatcher.BuildTarget(book, protectedEditions[0]);
            var names = target?.Names.Where(IsSpecificNarratorName).ToList();
            return names?.Count > 0 ? names : null;
        }

        private static List<string> GetExplicitReleaseNarrators(RemoteBook subject)
        {
            // Only explicit narrator metadata counts (indexer field, parsed field or a "narrated by" label
            // in the title). Trailing unlabelled name tokens are too weak to justify a rejection.
            var candidates = new[]
            {
                subject.Release.Narrator,
                subject.ParsedBookInfo?.Narrator,
                PreferredNarratorMatcher.ExtractNarratorFromFields(new[] { subject.Release.Title })
            };

            foreach (var text in candidates)
            {
                if (string.IsNullOrWhiteSpace(text))
                {
                    continue;
                }

                var names = ReleaseNarratorEvidenceExtractor.ExtractNames(null, text).Names
                    .Where(IsSpecificNarratorName)
                    .ToList();
                if (names.Count > 0)
                {
                    return names;
                }
            }

            return new List<string>();
        }

        private static bool IsSpecificNarratorName(string name)
        {
            if (string.IsNullOrWhiteSpace(name))
            {
                return false;
            }

            var normalized = string.Join(" ", name.Split((char[])null, System.StringSplitOptions.RemoveEmptyEntries));
            return !GenericNarratorNames.Contains(normalized);
        }

        private static BookMediaType? ResolveMediaType(RemoteBook subject, SearchCriteriaBase searchCriteria)
        {
            var detected = QualityMediaTypeHelper.DetectMediaType(subject?.ParsedBookInfo?.Quality?.Quality, subject?.Release);
            if (detected.HasValue)
            {
                return detected;
            }

            var hasResolvedIdentity = subject?.SearchCriteriaMatch?.IsMatch == true;
            if (!hasResolvedIdentity)
            {
                var releaseTitle = subject?.Release?.Title?.Trim();
                var parsedBookTitle = subject?.ParsedBookInfo?.BookTitle?.Trim();
                var parsedAuthor = subject?.ParsedBookInfo?.AuthorName?.Trim();
                hasResolvedIdentity = !string.IsNullOrWhiteSpace(parsedBookTitle) &&
                                     !string.IsNullOrWhiteSpace(parsedAuthor) &&
                                     !string.Equals(parsedBookTitle, releaseTitle, System.StringComparison.OrdinalIgnoreCase);
            }

            if (!hasResolvedIdentity)
            {
                return null;
            }

            var subjectBooks = (subject?.Books ?? Enumerable.Empty<Book>())
                .Where(book => book != null)
                .ToList();
            return subjectBooks.Count > 0
                ? GetSingleMediaType(subjectBooks)
                : GetSingleMediaType(searchCriteria?.Books);
        }

        private static BookMediaType? GetSingleMediaType(IEnumerable<Book> books)
        {
            var mediaTypes = (books ?? Enumerable.Empty<Book>())
                .Where(book => book != null)
                .Select(book => book.MediaType)
                .Distinct()
                .Take(2)
                .ToList();

            return mediaTypes.Count == 1 ? mediaTypes[0] : null;
        }
    }
}

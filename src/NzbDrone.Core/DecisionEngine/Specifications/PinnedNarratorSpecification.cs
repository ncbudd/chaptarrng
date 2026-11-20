using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
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
    /// being ranked by the narrator custom formats. A full name of another edition's narrator, or an
    /// Audible ASIN the library knows as another recording, counts as evidence too. The rejection can
    /// be bypassed from a manual search.
    /// </summary>
    public class PinnedNarratorSpecification : IDecisionEngineSpecification
    {
        // Audible ASINs as indexers put them in titles: "Pride and Prejudice {B0FBS2CPR7}".
        private static readonly Regex AsinInTitleRegex = new Regex(@"(?<![A-Za-z0-9])B0[0-9A-Z]{8}(?![A-Za-z0-9])", RegexOptions.Compiled);

        private readonly IEditionService _editionService;
        private readonly Logger _logger;

        public PinnedNarratorSpecification(IEditionService editionService, Logger logger)
        {
            _editionService = editionService;
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

            var pinnedNarrators = targets.SelectMany(target => target).Distinct(System.StringComparer.OrdinalIgnoreCase).ToList();
            var releaseNarrators = GetExplicitReleaseNarrators(subject);
            if (releaseNarrators.Count == 0)
            {
                releaseNarrators = GetOtherEditionNarratorsNamedInTitle(books, release.Title, pinnedNarrators);
                if (releaseNarrators.Count > 0)
                {
                    _logger.Debug("[PINNED_NARRATOR] Release title names the narrator of another edition of this book: {0}",
                        CleanseLogMessage.Cleanse(string.Join(", ", releaseNarrators)));
                }
            }

            if (releaseNarrators.Count == 0)
            {
                releaseNarrators = GetNarratorsOfAsinInTitle(books, release.Title, pinnedNarrators);
                if (releaseNarrators.Count > 0)
                {
                    _logger.Debug("[PINNED_NARRATOR] Release title carries the ASIN of an edition narrated by: {0}",
                        CleanseLogMessage.Cleanse(string.Join(", ", releaseNarrators)));
                }
            }

            if (releaseNarrators.Count == 0)
            {
                _logger.Trace("[PINNED_NARRATOR] No specific narrator found in release metadata, allowing");
                return Decision.Accept();
            }

            var everyPinnedNarratorMatches = pinnedNarrators.All(name =>
                releaseNarrators.Any(narrator => NarratorNameMatcher.IsMatch(narrator, name)));
            var everyReleaseNarratorMatches = releaseNarrators.All(narrator =>
                pinnedNarrators.Any(name => NarratorNameMatcher.IsMatch(narrator, name)));
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

        /// <summary>
        /// An unlabelled name in a release title is weak evidence in general, but a full name (two or
        /// more words) that is the narrator of another audiobook edition of the same book is specific:
        /// "...The.Fellowship.of.the.Ring.Rob.Inglis-PoF" for a book pinned to Andy Serkis. Returns those
        /// names, or nothing when the title also names a pinned narrator.
        /// </summary>
        private static List<string> GetOtherEditionNarratorsNamedInTitle(IEnumerable<Book> books, string title, List<string> pinnedNarrators)
        {
            var normalizedTitle = $" {NormalizeForNameSearch(title)} ";
            if (normalizedTitle.Trim().Length == 0 ||
                pinnedNarrators.Any(name => TitleContainsFullName(normalizedTitle, name)))
            {
                return new List<string>();
            }

            return books
                .Where(book => book?.Editions != null)
                .SelectMany(book => book.Editions)
                .Where(PreferredNarratorMatcher.IsAudiobookEdition)
                .SelectMany(edition => ReleaseNarratorEvidenceExtractor.ExtractNames(edition.NarratorNames, edition.Narrator).Names)
                .Where(IsSpecificNarratorName)
                .Where(name => !pinnedNarrators.Any(pinned => NarratorNameMatcher.IsMatch(name, pinned)))
                .Where(name => TitleContainsFullName(normalizedTitle, name))
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .ToList();
        }

        /// <summary>
        /// An Audible ASIN in a release title identifies one recording. When the library knows that
        /// ASIN as an audiobook edition (of this book, or of a duplicate book for the same work, such
        /// as an Audible-only listing) and none of its narrators is a pinned narrator, the release is
        /// another recording: "Pride and Prejudice {B0FBS2CPR7}" is the full-cast edition, not the
        /// pinned Kate Reading one. Returns nothing when the ASIN is unknown, belongs to the pinned
        /// edition, has no narrator data, or any matching edition shares a pinned narrator.
        /// </summary>
        private List<string> GetNarratorsOfAsinInTitle(IEnumerable<Book> books, string title, List<string> pinnedNarrators)
        {
            var none = new List<string>();
            if (_editionService == null || string.IsNullOrWhiteSpace(title))
            {
                return none;
            }

            var asins = AsinInTitleRegex.Matches(title)
                .Select(match => match.Value)
                .Distinct(StringComparer.Ordinal)
                .Take(3)
                .ToList();
            if (asins.Count == 0)
            {
                return none;
            }

            var pinnedAsins = new HashSet<string>(
                books.Where(book => book != null)
                    .SelectMany(book => EditionPinPolicy.GetProtectedEditions(book, book.Editions))
                    .SelectMany(GetAsins),
                StringComparer.OrdinalIgnoreCase);

            var names = new List<string>();
            foreach (var asin in asins)
            {
                if (pinnedAsins.Contains(asin))
                {
                    return none;
                }

                List<Edition> editions;
                try
                {
                    editions = _editionService.GetEditionsByProviderAndId("az", asin)
                        .Where(PreferredNarratorMatcher.IsAudiobookEdition)
                        .ToList();
                }
                catch (Exception ex)
                {
                    _logger.Debug(ex, "[PINNED_NARRATOR] ASIN lookup failed, ignoring the ASIN");
                    return none;
                }

                foreach (var edition in editions)
                {
                    var editionNarrators = ReleaseNarratorEvidenceExtractor.ExtractNames(edition.NarratorNames, edition.Narrator).Names
                        .Where(IsSpecificNarratorName)
                        .ToList();
                    if (editionNarrators.Count == 0 ||
                        editionNarrators.Any(name => pinnedNarrators.Any(pinned => NarratorNameMatcher.IsMatch(name, pinned))))
                    {
                        return none;
                    }

                    names.AddRange(editionNarrators);
                }
            }

            return names.Distinct(StringComparer.OrdinalIgnoreCase).ToList();
        }

        private static IEnumerable<string> GetAsins(Edition edition)
        {
            if (edition == null)
            {
                return Enumerable.Empty<string>();
            }

            return new[] { edition.Asin, edition.AudibleASIN }
                .Concat(edition.Asins ?? new List<string>())
                .Where(asin => !string.IsNullOrWhiteSpace(asin))
                .Select(asin => asin.Trim());
        }

        private static bool TitleContainsFullName(string normalizedTitle, string name)
        {
            var normalizedName = NormalizeForNameSearch(name);
            return normalizedName.Contains(' ') &&
                   normalizedTitle.Contains($" {normalizedName} ", StringComparison.Ordinal);
        }

        // Scene titles separate words with dots, dashes or underscores ("Rob.Inglis-PoF").
        private static string NormalizeForNameSearch(string text)
        {
            return string.IsNullOrWhiteSpace(text)
                ? string.Empty
                : Regex.Replace(text.ToLowerInvariant(), @"[^\p{L}\p{N}]+", " ").Trim();
        }

        private static bool IsSpecificNarratorName(string name)
        {
            return !string.IsNullOrWhiteSpace(name) && !NarratorNameMatcher.IsGenericNarratorLabel(name);
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

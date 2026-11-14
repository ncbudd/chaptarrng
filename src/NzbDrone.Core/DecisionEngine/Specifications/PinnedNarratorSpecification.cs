using System.Collections.Generic;
using System.Linq;
using NLog;
using NzbDrone.Core.Books;
using NzbDrone.Core.CustomFormats;
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

            var quality = subject.ParsedBookInfo?.Quality?.Quality;
            if (QualityMediaTypeHelper.DetectMediaType(quality, release) != BookMediaType.Audiobook)
            {
                return Decision.Accept();
            }

            var targets = new List<List<string>>();
            foreach (var book in books)
            {
                var target = GetPinnedTarget(book);
                if (target == null)
                {
                    // Any targeted book that is not pinned to a single narrated edition leaves the release open.
                    return Decision.Accept();
                }

                targets.Add(target);
            }

            var releaseNarrators = GetExplicitReleaseNarrators(subject);
            if (releaseNarrators.Count == 0)
            {
                _logger.Trace("[PINNED_NARRATOR] No narrator found for '{0}', allowing", release.Title);
                return Decision.Accept();
            }

            var matches = targets.Any(target => target.Any(name => releaseNarrators.Any(narrator => PreferredNarratorMatcher.IsNarratorNameMatch(narrator, name))));
            if (matches)
            {
                return Decision.Accept();
            }

            var wanted = string.Join(", ", targets.SelectMany(t => t).Distinct());
            return Decision.RejectSoftFilter(
                "Release narrator [{0}] does not match the pinned narrator [{1}]",
                "Narrator",
                string.Join(", ", releaseNarrators),
                wanted);
        }

        private static List<string> GetPinnedTarget(Book book)
        {
            if (book == null || book.AnyEditionOk)
            {
                return null;
            }

            var monitored = book.Editions?
                .Where(edition => edition != null && edition.Monitored && PreferredNarratorMatcher.IsAudiobookEdition(edition))
                .ToList();

            if (monitored == null || monitored.Count != 1)
            {
                return null;
            }

            var target = PreferredNarratorMatcher.BuildTarget(book, monitored[0]);
            return target?.Names.Count > 0 ? target.Names : null;
        }

        private static List<string> GetExplicitReleaseNarrators(RemoteBook subject)
        {
            // Only explicit narrator metadata counts (indexer field, parsed field or a "narrated by" label
            // in the title). Trailing unlabelled name tokens are too weak to justify a rejection.
            var text = subject.Release.Narrator;
            if (string.IsNullOrWhiteSpace(text))
            {
                text = subject.ParsedBookInfo?.Narrator;
            }

            if (string.IsNullOrWhiteSpace(text))
            {
                text = PreferredNarratorMatcher.ExtractNarratorFromFields(new[] { subject.Release.Title });
            }

            if (string.IsNullOrWhiteSpace(text))
            {
                return new List<string>();
            }

            return ReleaseNarratorEvidenceExtractor.ExtractNames(null, text).Names
                .Where(name => !string.IsNullOrWhiteSpace(name))
                .ToList();
        }
    }
}

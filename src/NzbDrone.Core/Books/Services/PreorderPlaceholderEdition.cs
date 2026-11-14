using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using NzbDrone.Common.Extensions;
using NzbDrone.Core.Books.Calibre;

namespace NzbDrone.Core.Books.Services
{
    /// <summary>
    /// Before release, providers often list a new book's edition under a placeholder title such as
    /// "A Court of Thorns and Roses 6". A request made then pins that edition, and the book is titled
    /// after its monitored edition, so searches keep using the placeholder after the real title is
    /// announced. This moves monitoring (and the pin) to the real edition when that is unambiguous.
    /// </summary>
    internal static class PreorderPlaceholderEdition
    {
        private static readonly Regex NumberedTitle = new Regex(@"^(?<prefix>.+?)\s*#?\s*(?<number>\d{1,2})$", RegexOptions.Compiled | RegexOptions.CultureInvariant);

        internal static bool IsPlaceholderTitle(string title, IReadOnlyCollection<string> seriesNames, string seriesPosition)
        {
            title = Normalize(title);
            if (title.Length == 0 || seriesNames == null || seriesNames.Count == 0)
            {
                return false;
            }

            var position = Normalize(seriesPosition).TrimStart('#').Trim();
            foreach (var series in seriesNames.Select(Normalize).Where(s => s.Length > 0))
            {
                if (position.Length > 0 &&
                    (string.Equals(title, $"{series} {position}", StringComparison.OrdinalIgnoreCase) ||
                     string.Equals(title, $"{series} #{position}", StringComparison.OrdinalIgnoreCase)))
                {
                    return true;
                }

                var match = NumberedTitle.Match(title);
                if (match.Success)
                {
                    var prefix = match.Groups["prefix"].Value.Trim();
                    if (prefix.Length > 0 && series.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
                    {
                        return true;
                    }
                }
            }

            return false;
        }

        /// <summary>
        /// Moves the monitored flag (and the ManualAdd pin, if the placeholder carried it) to the single
        /// matching real edition. Returns the edition monitoring moved to, or null when nothing changed.
        /// </summary>
        internal static Edition TryMove(List<Edition> editions, Book book, IReadOnlyDictionary<int, int> fileCountsByEditionId)
        {
            if (editions == null || book == null)
            {
                return null;
            }

            var list = editions.Where(e => e != null).ToList();
            var monitored = list.Where(e => e.Monitored).ToList();
            if (monitored.Count != 1)
            {
                return null;
            }

            var placeholder = monitored[0];

            // Never touch a book that has files (book level or any edition).
            if ((book.BookFiles?.Any() ?? false) ||
                list.Any(e => (e.BookFiles?.Count ?? 0) > 0 ||
                              (fileCountsByEditionId != null && fileCountsByEditionId.TryGetValue(e.Id, out var c) && c > 0)))
            {
                return null;
            }

            var seriesNames = GetSeriesNames(book);
            if (!IsPlaceholderTitle(placeholder.Title, seriesNames, book.SeriesPosition))
            {
                return null;
            }

            var narrators = GetNarrators(placeholder);
            var candidates = list
                .Where(e => !ReferenceEquals(e, placeholder) &&
                            e.ForeignEditionId != placeholder.ForeignEditionId &&
                            Normalize(e.Title).Length > 0 &&
                            !IsPlaceholderTitle(e.Title, seriesNames, book.SeriesPosition) &&
                            SameFormat(e, placeholder) &&
                            SameLanguage(e, placeholder) &&
                            (narrators.Count == 0 || narrators.SetEquals(GetNarrators(e))))
                .ToList();

            if (candidates.Count != 1)
            {
                return null;
            }

            var real = candidates[0];
            real.Monitored = true;
            real.ManualAdd = placeholder.ManualAdd;
            placeholder.Monitored = false;
            placeholder.ManualAdd = false;

            return real;
        }

        private static List<string> GetSeriesNames(Book book)
        {
            var names = new List<string>();
            if (book.SeriesName.IsNotNullOrWhiteSpace())
            {
                names.Add(book.SeriesName);
            }

            try
            {
                foreach (var link in book.SeriesLinks ?? new List<SeriesBookLink>())
                {
                    var title = link?.Series?.Value?.Title;
                    if (title.IsNotNullOrWhiteSpace())
                    {
                        names.Add(title);
                    }
                }
            }
            catch
            {
                // Series links are best-effort here; the denormalized SeriesName still applies.
            }

            return names.Distinct(StringComparer.OrdinalIgnoreCase).ToList();
        }

        private static bool SameFormat(Edition a, Edition b)
        {
            if (a.ReadingFormatId.HasValue && b.ReadingFormatId.HasValue)
            {
                return a.ReadingFormatId == b.ReadingFormatId;
            }

            return a.ReadingFormatId == b.ReadingFormatId &&
                   string.Equals(Normalize(a.Format), Normalize(b.Format), StringComparison.OrdinalIgnoreCase);
        }

        private static bool SameLanguage(Edition a, Edition b)
        {
            return string.Equals(
                a.Language?.CanonicalizeLanguage() ?? string.Empty,
                b.Language?.CanonicalizeLanguage() ?? string.Empty,
                StringComparison.OrdinalIgnoreCase);
        }

        private static HashSet<string> GetNarrators(Edition edition)
        {
            IEnumerable<string> names = edition.NarratorNames != null && edition.NarratorNames.Any()
                ? edition.NarratorNames
                : (edition.Narrator ?? string.Empty).Split(new[] { ',', ';', '&' }, StringSplitOptions.RemoveEmptyEntries);

            return new HashSet<string>(
                names.Select(n => Normalize(n).ToLowerInvariant()).Where(n => n.Length > 0),
                StringComparer.Ordinal);
        }

        private static string Normalize(string value)
        {
            return Regex.Replace(value ?? string.Empty, @"\s+", " ").Trim();
        }
    }
}

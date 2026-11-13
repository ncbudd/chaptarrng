using System;
using System.Collections.Generic;
using System.Linq;
using FluentValidation;
using FluentValidation.Results;
using NzbDrone.Common.Extensions;
using NzbDrone.Core.Annotations;
using NzbDrone.Core.Books;
using NzbDrone.Core.Parser.Model;
using NzbDrone.Core.Profiles.Metadata;
using NzbDrone.Core.Profiles.Qualities;
using NzbDrone.Core.RootFolders;
using NzbDrone.Core.Tags;
using NzbDrone.Core.Validation;

namespace NzbDrone.Core.ImportLists.Goodreads
{
    public interface IGoodreadsDualMediaImportListSettings : IImportListSettings, IMediaTypeRootFolderSettings
    {
        bool MonitorAudiobooks { get; set; }
        bool MonitorEbooks { get; set; }
        int ImportLimit { get; set; }
        int AudiobookQualityProfileId { get; set; }
        int EbookQualityProfileId { get; set; }
        int AudiobookMetadataProfileId { get; set; }
        int EbookMetadataProfileId { get; set; }
        List<int> AudiobookTags { get; set; }
        List<int> EbookTags { get; set; }
    }

    public static class GoodreadsDualMediaImportListSettingsValidator
    {
        public static void AddDualMediaRules<TSettings>(this AbstractValidator<TSettings> validator)
            where TSettings : IGoodreadsDualMediaImportListSettings
        {
            validator.RuleFor(c => c)
                .Must(c => c.MonitorAudiobooks || c.MonitorEbooks)
                .WithMessage("Select at least one media type to monitor")
                .WithState(_ => NzbDroneValidationState.ForMessage("server.message.m1f70cc839b57"));

            validator.RuleFor(c => c.ImportLimit)
                .GreaterThanOrEqualTo(0)
                .WithMessage("Import limit must be 0 or greater")
                .WithState(_ => NzbDroneValidationState.ForMessage("server.message.mb2b9d54cbbeb"));

            validator.RuleFor(c => c.AudiobookRootFolderPath)
                .NotEmpty()
                .When(c => c.MonitorAudiobooks)
                .WithMessage("Audiobook root folder is required when monitoring audiobooks")
                .WithState(_ => NzbDroneValidationState.ForMessage("server.message.m6d69cc1ffcc4"));

            validator.RuleFor(c => c.EbookRootFolderPath)
                .NotEmpty()
                .When(c => c.MonitorEbooks)
                .WithMessage("Ebook root folder is required when monitoring ebooks")
                .WithState(_ => NzbDroneValidationState.ForMessage("server.message.m7a3bf57a5ad5"));
        }
    }

    internal static class GoodreadsDualMediaImportListActions
    {
        public static object HandleRequestAction(
            string action,
            Lazy<IQualityProfileService> qualityProfileService,
            Lazy<IMetadataProfileService> metadataProfileService,
            Lazy<ITagService> tagService)
        {
            if (action.IsNullOrWhiteSpace())
            {
                return null;
            }

            if (action == "getAudiobookQualityProfiles")
            {
                return new
                {
                    options = BuildSelectOptions(qualityProfileService.Value.GetByType(ProfileType.Audiobook).Select(p => (p.Id, p.Name)), includeDefault: true)
                };
            }

            if (action == "getEbookQualityProfiles")
            {
                return new
                {
                    options = BuildSelectOptions(qualityProfileService.Value.GetByType(ProfileType.Ebook).Select(p => (p.Id, p.Name)), includeDefault: true)
                };
            }

            if (action == "getAudiobookMetadataProfiles")
            {
                return new
                {
                    options = BuildSelectOptions(metadataProfileService.Value.All()
                        .Where(p => p.ProfileType == MetadataProfileType.General || p.ProfileType == MetadataProfileType.Audiobook)
                        .Select(p => (p.Id, p.Name)), includeDefault: true)
                };
            }

            if (action == "getEbookMetadataProfiles")
            {
                return new
                {
                    options = BuildSelectOptions(metadataProfileService.Value.All()
                        .Where(p => p.ProfileType == MetadataProfileType.General || p.ProfileType == MetadataProfileType.Ebook)
                        .Select(p => (p.Id, p.Name)), includeDefault: true)
                };
            }

            if (action == "getTags")
            {
                return new
                {
                    options = tagService.Value.All()
                        .OrderBy(t => t.Label)
                        .Select(t => new
                        {
                            Value = t.Id,
                            Name = t.Label
                        })
                        .ToList()
                };
            }

            return null;
        }

        public static IEnumerable<ValidationFailure> TestRootFolderConfig(
            IGoodreadsDualMediaImportListSettings settings,
            IRootFolderService rootFolderService,
            IRootFolderSettingsResolver rootFolderSettingsResolver)
        {
            var failures = new List<ValidationFailure>();

            if (settings == null)
            {
                return failures;
            }

            if (settings.MonitorAudiobooks)
            {
                failures.AddIfNotNull(TestRootFolder(
                    nameof(settings.AudiobookRootFolderPath),
                    settings.AudiobookRootFolderPath,
                    BookMediaType.Audiobook,
                    settings.AudiobookQualityProfileId,
                    settings.AudiobookMetadataProfileId,
                    rootFolderService,
                    rootFolderSettingsResolver));
            }

            if (settings.MonitorEbooks)
            {
                failures.AddIfNotNull(TestRootFolder(
                    nameof(settings.EbookRootFolderPath),
                    settings.EbookRootFolderPath,
                    BookMediaType.Ebook,
                    settings.EbookQualityProfileId,
                    settings.EbookMetadataProfileId,
                    rootFolderService,
                    rootFolderSettingsResolver));
            }

            return failures;
        }

        private static ValidationFailure TestRootFolder(
            string fieldName,
            string rootFolderPath,
            BookMediaType mediaType,
            int overrideQualityProfileId,
            int overrideMetadataProfileId,
            IRootFolderService rootFolderService,
            IRootFolderSettingsResolver rootFolderSettingsResolver)
        {
            if (rootFolderPath.IsNullOrWhiteSpace())
            {
                return NzbDroneValidationFailure.ForMessage(fieldName, "Root folder is required", "server.message.m305661a25dbf");
            }

            var rootFolder = rootFolderService.GetBestRootFolder(rootFolderPath);
            if (rootFolder == null)
            {
                return NzbDroneValidationFailure.ForMessage(fieldName, $"Root folder '{rootFolderPath}' is not configured in Chaptarr", "server.message.m6db923fcd485", new { value0 = rootFolderPath });
            }

            if (mediaType == BookMediaType.Audiobook && rootFolder.FolderType == FolderType.Ebook)
            {
                return NzbDroneValidationFailure.ForMessage(fieldName, "Selected root folder is Ebook-only; choose an Audiobook or Mixed root folder", "server.message.m45461e168bdc");
            }

            if (mediaType == BookMediaType.Ebook && rootFolder.FolderType == FolderType.Audiobook)
            {
                return NzbDroneValidationFailure.ForMessage(fieldName, "Selected root folder is Audiobook-only; choose an Ebook or Mixed root folder", "server.message.mb5750cd165f2");
            }

            var resolved = rootFolderSettingsResolver.ResolveSettings(rootFolder, mediaType);
            if (resolved == null || !resolved.IsConfigured)
            {
                return NzbDroneValidationFailure.ForMessage(fieldName, $"Selected root folder '{rootFolder.Path}' does not have {mediaType} defaults configured", "server.message.mf2463602ee31", new { value0 = rootFolder.Path, value1 = mediaType });
            }

            if (overrideQualityProfileId <= 0 && (resolved.QualityProfileId ?? 0) <= 0)
            {
                return NzbDroneValidationFailure.ForMessage(fieldName, $"Selected root folder '{rootFolder.Path}' is missing a {mediaType} quality profile default", "server.message.m0df8751db78b", new { value0 = rootFolder.Path, value1 = mediaType });
            }

            if (overrideMetadataProfileId <= 0 && (resolved.MetadataProfileId ?? 0) <= 0)
            {
                return NzbDroneValidationFailure.ForMessage(fieldName, $"Selected root folder '{rootFolder.Path}' is missing a {mediaType} metadata profile default", "server.message.md5295352b8ae", new { value0 = rootFolder.Path, value1 = mediaType });
            }

            return null;
        }

        private static List<object> BuildSelectOptions(IEnumerable<(int id, string name)> items, bool includeDefault)
        {
            var options = new List<object>();

            if (includeDefault)
            {
                options.Add(new
                {
                    Value = 0,
                    Name = "Use root folder defaults",
                    LocalizationKey = "UseRootFolderDefaults"
                });
            }

            options.AddRange(items
                .OrderBy(i => i.name)
                .Select(i => new
                {
                    Value = i.id,
                    Name = i.name
                }));

            return options;
        }
    }

    internal static class GoodreadsImportListLimit
    {
        public static bool IsEnabled(int limit)
        {
            return limit > 0;
        }

        public static bool HasReached(int count, int limit)
        {
            return IsEnabled(limit) && count >= limit;
        }

        public static bool TryAdd(
            IList<ImportListItemInfo> target,
            ImportListItemInfo item,
            ISet<string> seenSourceBooks,
            int limit)
        {
            if (item == null || HasReached(target.Count, limit))
            {
                return false;
            }

            if (IsEnabled(limit))
            {
                var sourceKey = GetSourceBookKey(item);
                if (sourceKey.IsNotNullOrWhiteSpace() &&
                    seenSourceBooks != null &&
                    !seenSourceBooks.Add(sourceKey))
                {
                    return false;
                }
            }

            target.Add(item);
            return true;
        }

        private static string GetSourceBookKey(ImportListItemInfo item)
        {
            if (item.BookProviderId.IsNotNullOrWhiteSpace())
            {
                return ImportListProviderIdHelper.Normalize(item.BookProviderId, "gr");
            }

            if (item.EditionProviderId.IsNotNullOrWhiteSpace())
            {
                return ImportListProviderIdHelper.Normalize(item.EditionProviderId, "gr");
            }

            if (item.Book.IsNotNullOrWhiteSpace() || item.Author.IsNotNullOrWhiteSpace())
            {
                return $"{item.Author?.Trim()}::{item.Book?.Trim()}".ToLowerInvariant();
            }

            return null;
        }
    }
}

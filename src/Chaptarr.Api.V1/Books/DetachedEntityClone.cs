using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Newtonsoft.Json;
using Newtonsoft.Json.Serialization;
using NzbDrone.Common.Serializer;
using NzbDrone.Core.Books;
using NzbDrone.Core.Datastore;
using NzbDrone.Core.MediaFiles;

namespace Chaptarr.Api.V1.Books
{
    /// <summary>
    /// Copies the stored state of a book or edition for PUT /book without walking the loaded
    /// entity graph. A plain JsonClone follows navigation properties (Book.Editions -> Edition.Book,
    /// BookFile.Edition, lazy loaders that query on access) and the entities compare by value, so
    /// Newtonsoft reports a self referencing loop for every book that has editions.
    /// Navigation properties are skipped here; the book copy gets its loaded relations back by
    /// reference, and every edition is copied the same way.
    /// </summary>
    public static class DetachedEntityClone
    {
        private static readonly Type[] NavigationTypes =
        {
            typeof(Book),
            typeof(Edition),
            typeof(NzbDrone.Core.Books.Author),
            typeof(BookFile),
            typeof(SeriesBookLink),
            typeof(NzbDrone.Core.Books.Series),
            typeof(Narrator)
        };

        private static readonly JsonSerializerSettings Settings = CreateSettings();

        public static Edition Clone(Edition source)
        {
            if (source == null)
            {
                return null;
            }

            return CopyScalars(source);
        }

        public static Book Clone(Book source)
        {
            if (source == null)
            {
                return null;
            }

            var authorId = source.AuthorId;
            var copy = CopyScalars(source);

            if (source.LazyAuthor?.IsLoaded == true)
            {
                copy.Author = source.Author;
            }

            copy.AuthorId = authorId;

            if (source.LazyEditions?.IsLoaded == true)
            {
                copy.Editions = source.Editions?.Select(Clone).ToList();
            }

            if (source.LazyBookFiles?.IsLoaded == true)
            {
                copy.BookFiles = source.BookFiles;
            }

            if (source.LazySeriesLinks?.IsLoaded == true)
            {
                copy.SeriesLinks = source.SeriesLinks;
            }

            copy.NarratorEntity = source.NarratorEntity;
            copy.WantedNarrator = source.WantedNarrator;
            return copy;
        }

        private static T CopyScalars<T>(T source)
        {
            var json = JsonConvert.SerializeObject(source, Settings);
            return JsonConvert.DeserializeObject<T>(json, Settings);
        }

        private static JsonSerializerSettings CreateSettings()
        {
            var settings = Json.GetSerializerSettings();
            settings.ContractResolver = new DetachedContractResolver();
            settings.Formatting = Formatting.None;
            return settings;
        }

        internal static bool IsNavigationType(Type type)
        {
            if (type == null || type == typeof(string))
            {
                return false;
            }

            if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(LazyLoaded<>))
            {
                return true;
            }

            if (typeof(ILazyLoaded).IsAssignableFrom(type))
            {
                return true;
            }

            if (NavigationTypes.Any(navigation => navigation.IsAssignableFrom(type)))
            {
                return true;
            }

            var element = type.IsArray
                ? type.GetElementType()
                : type.GetInterfaces()
                    .Concat(type.IsInterface ? new[] { type } : Array.Empty<Type>())
                    .Where(i => i.IsGenericType && i.GetGenericTypeDefinition() == typeof(IEnumerable<>))
                    .Select(i => i.GetGenericArguments()[0])
                    .FirstOrDefault();

            return element != null && element != type && IsNavigationType(element);
        }

        private sealed class DetachedContractResolver : CamelCasePropertyNamesContractResolver
        {
            protected override JsonProperty CreateProperty(MemberInfo member, MemberSerialization memberSerialization)
            {
                var property = base.CreateProperty(member, memberSerialization);

                // The models mark computed and lazy members with System.Text.Json's [JsonIgnore]
                // (AuthorId, NarratorName, HasFiles, Lazy*); Newtonsoft does not read that attribute.
                if (IsNavigationType(property.PropertyType) ||
                    member.GetCustomAttribute<global::System.Text.Json.Serialization.JsonIgnoreAttribute>() != null)
                {
                    property.Ignored = true;
                    property.ShouldSerialize = _ => false;
                }

                return property;
            }
        }
    }
}

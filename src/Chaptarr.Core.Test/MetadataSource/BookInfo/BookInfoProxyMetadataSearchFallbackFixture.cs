using System;
using System.Collections.Generic;
using System.Reflection;
using Moq;
using NLog;
using NUnit.Framework;
using NzbDrone.Common.Cache;
using NzbDrone.Core.Books;
using NzbDrone.Core.Configuration;
using NzbDrone.Core.MetadataSource;
using NzbDrone.Core.MetadataSource.BookInfo;
using NzbDrone.Core.MetadataSource.Hardcover;
using GoodreadsException = NzbDrone.Core.MetadataSource.Goodreads.GoodreadsException;
using IGoodreadsSearchProxy = NzbDrone.Core.MetadataSource.Goodreads.IGoodreadsSearchProxy;
using SearchJsonResource = NzbDrone.Core.MetadataSource.Goodreads.SearchJsonResource;

namespace Chaptarr.Core.Test.MetadataSource.BookInfo
{
    // A metadata server that answers id lookups but has no free-text search (api2.chaptarr.com
    // answers 404 for /search) must not fail ISBN and title lookups when Hardcover can answer them.
    [TestFixture]
    public class BookInfoProxyMetadataSearchFallbackFixture
    {
        private class ConfigServiceProxy : DispatchProxy
        {
            protected override object Invoke(MethodInfo targetMethod, object[] args)
            {
                if (targetMethod?.Name == "IsDefined")
                {
                    return false;
                }

                return targetMethod?.Name switch
                {
                    "get_MetadataServerUrl" => "http://metadata",
                    _ when targetMethod?.Name.StartsWith("get_", StringComparison.Ordinal) == true =>
                        targetMethod.ReturnType.IsValueType ? Activator.CreateInstance(targetMethod.ReturnType) : null,
                    _ => throw new NotImplementedException($"Test proxy does not implement {targetMethod?.Name}")
                };
            }
        }

        // Hardcover token configured, but Hardcover is not the selected catalog (not native).
        private sealed class TokenOnlyHardcoverMetadataProxy : IHardcoverMetadataProxy
        {
            public bool IsConfigured { get; set; } = true;
            public bool IsNativeEnabled => false;
            public List<string> Searches { get; } = new();

            public List<SearchJsonResource> Search(string query, bool interactiveSearch = false)
            {
                Searches.Add(query);
                return new List<SearchJsonResource>
                {
                    new SearchJsonResource { WorkId = 101, BookId = 201, Title = "Native Book" }
                };
            }

            public Newtonsoft.Json.Linq.JObject ExecuteSearchGraphQl(
                string operationName,
                string query,
                Newtonsoft.Json.Linq.JObject variables,
                bool interactiveSearch = false)
            {
                throw new NotSupportedException();
            }

            public AuthorResource GetAuthor(string foreignAuthorId, bool interactiveSearch = false) => throw new NotSupportedException();

            public WorkResource GetWork(string foreignWorkId, bool interactiveSearch = false) => new()
            {
                ForeignId = 101,
                Title = "Native Book",
                Authors = new List<AuthorResource> { new() { ForeignId = 42, Name = "Native Author" } },
                Books = new List<BookResource>
                {
                    new()
                    {
                        ForeignId = 201,
                        Title = "Native Book Edition",
                        Isbn13 = "9780000000001",
                        Format = "Audiobook",
                        Contributors = new List<ContributorResource> { new() { ForeignId = 42 } }
                    }
                },
                Series = new List<SeriesResource>()
            };

            public WorkResource GetEdition(string foreignEditionId, bool interactiveSearch = false) => throw new NotSupportedException();
        }

        private static BookInfoProxy CreateProxy(IHardcoverMetadataProxy hardcover)
        {
            var configService = DispatchProxy.Create<IConfigService, ConfigServiceProxy>();
            var logger = LogManager.GetCurrentClassLogger();

            var metadataSearch = new Mock<IGoodreadsSearchProxy>();
            var notFound = new GoodreadsException("Search for '{0}' failed. Unable to communicate with the metadata source.", new Exception("404"), "term");
            metadataSearch.Setup(x => x.Search(It.IsAny<string>())).Throws(notFound);
            metadataSearch.Setup(x => x.SearchMetadataApi(It.IsAny<string>())).Throws(notFound);

            var additional = new Mock<IAdditionalBookMetadataProxy>();
            additional.Setup(x => x.Search(It.IsAny<string>())).Returns(new List<Book>());
            additional.Setup(x => x.ApplyFieldSourcePreferences(It.IsAny<Book>())).Returns<Book>(book => book);
            additional.Setup(x => x.ApplyAuthorImageSourcePreference(It.IsAny<Author>(), It.IsAny<Book>()))
                .Returns<Author, Book>((author, _) => author);

            return new BookInfoProxy(
                httpClient: null,
                cachedHttpClient: null,
                goodreadsSearchProxy: metadataSearch.Object,
                hardcoverSearchClient: null,
                audibleCatalogProxy: null,
                authorService: Mock.Of<IAuthorService>(service => service.FindByProviderId(It.IsAny<string>(), It.IsAny<string>()) == null),
                bookService: Mock.Of<IBookService>(service => service.FindByProviderId(It.IsAny<string>(), It.IsAny<string>()) == null),
                editionService: Mock.Of<IEditionService>(),
                configService: configService,
                requestBuilder: new MetadataRequestBuilder(configService),
                logger: logger,
                cacheManager: new CacheManager(),
                metadataServerHealthGate: new MetadataServerHealthGate(configService, new MetadataServerHealthService(logger), logger),
                additionalBookMetadataProxy: additional.Object,
                hardcoverMetadataProxy: hardcover);
        }

        [TestCase("isbn:9780000000001", "9780000000001")]
        [TestCase("9780000000001", "9780000000001")]
        [TestCase("Native Book", "native book")]
        public void should_search_hardcover_when_the_metadata_server_cannot_search(string term, string expectedQuery)
        {
            var hardcover = new TokenOnlyHardcoverMetadataProxy();
            var proxy = CreateProxy(hardcover);

            var results = proxy.SearchForNewBook(term, null, mediaType: BookMediaType.Audiobook);

            Assert.That(hardcover.Searches, Is.EqualTo(new[] { expectedQuery }));
            Assert.That(results, Has.Count.EqualTo(1));
            Assert.That(results[0].Title, Is.EqualTo("Native Book"));
            Assert.That(results[0].MediaType, Is.EqualTo(BookMediaType.Audiobook));
        }

        [Test]
        public void should_still_report_the_metadata_server_failure_without_a_hardcover_token()
        {
            var hardcover = new TokenOnlyHardcoverMetadataProxy { IsConfigured = false };
            var proxy = CreateProxy(hardcover);

            Assert.Throws<GoodreadsException>(() => proxy.SearchForNewBook("Native Book", null, mediaType: BookMediaType.Audiobook));
            Assert.That(hardcover.Searches, Is.Empty);
        }
    }
}

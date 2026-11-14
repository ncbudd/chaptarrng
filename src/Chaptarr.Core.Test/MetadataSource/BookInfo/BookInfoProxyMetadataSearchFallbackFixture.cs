using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Reflection;
using System.Threading.Tasks;
using Chaptarr.Http.ErrorManagement;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Http.Features;
using Microsoft.AspNetCore.Routing;
using DefaultHttpContext = Microsoft.AspNetCore.Http.DefaultHttpContext;
using Endpoint = Microsoft.AspNetCore.Http.Endpoint;
using Moq;
using NLog;
using NLog.Config;
using NLog.Targets;
using NUnit.Framework;
using NzbDrone.Common.Cache;
using NzbDrone.Common.Http;
using NzbDrone.Core.Books;
using NzbDrone.Core.Configuration;
using NzbDrone.Core.Http;
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
    [NonParallelizable]
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

        private sealed class TestExceptionHandlerPathFeature : IExceptionHandlerPathFeature
        {
            public TestExceptionHandlerPathFeature(Exception error)
            {
                Error = error;
            }

            public Exception Error { get; }
            public string Path => "/api/v1/book/lookup";
            public Endpoint Endpoint => null;
            public RouteValueDictionary RouteValues { get; } = new();
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
                    },
                    new()
                    {
                        ForeignId = 202,
                        Title = "Native Book Alternate Edition",
                        Isbn13 = "9780000000002",
                        Format = "Audiobook",
                        Contributors = new List<ContributorResource> { new() { ForeignId = 42 } }
                    }
                },
                Series = new List<SeriesResource>()
            };

            public WorkResource GetEdition(string foreignEditionId, bool interactiveSearch = false) => throw new NotSupportedException();
        }

        private static GoodreadsException MetadataSearchException(HttpStatusCode statusCode)
        {
            return new GoodreadsException("Metadata server search failed with HTTP status {0}.", statusCode);
        }

        [Test]
        public void should_format_upstream_status_in_metadata_search_exception()
        {
            var exception = MetadataSearchException(HttpStatusCode.NotFound);

            Assert.That(exception.Message, Is.EqualTo("Metadata server search failed with HTTP status NotFound."));
            Assert.That(exception.UpstreamStatusCode, Is.EqualTo(HttpStatusCode.NotFound));
        }

        private static BookInfoProxy CreateProxy(IHardcoverMetadataProxy hardcover, GoodreadsException searchException = null)
        {
            var configService = DispatchProxy.Create<IConfigService, ConfigServiceProxy>();
            var logger = LogManager.GetCurrentClassLogger();

            var metadataSearch = new Mock<IGoodreadsSearchProxy>();
            var notFound = searchException ?? MetadataSearchException(HttpStatusCode.NotFound);
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

        [Test]
        public void should_not_search_hardcover_when_the_metadata_server_returns_a_transient_error()
        {
            var hardcover = new TokenOnlyHardcoverMetadataProxy();
            var proxy = CreateProxy(hardcover, MetadataSearchException(HttpStatusCode.ServiceUnavailable));

            Assert.Throws<GoodreadsException>(() => proxy.SearchForNewBook("Native Book", null, mediaType: BookMediaType.Audiobook));
            Assert.That(hardcover.Searches, Is.Empty);
        }

        [Test]
        public void should_return_one_hardcover_edition_when_all_editions_were_not_requested()
        {
            var proxy = CreateProxy(new TokenOnlyHardcoverMetadataProxy());

            var results = proxy.SearchForNewBook("Native Book", null, getAllEditions: false, mediaType: BookMediaType.Audiobook);

            Assert.That(results, Has.Count.EqualTo(1));
            Assert.That(results[0].Editions, Has.Count.EqualTo(1));
        }

        [Test]
        public void should_return_all_hardcover_editions_when_requested()
        {
            var proxy = CreateProxy(new TokenOnlyHardcoverMetadataProxy());

            var results = proxy.SearchForNewBook("Native Book", null, getAllEditions: true, mediaType: BookMediaType.Audiobook);

            Assert.That(results, Has.Count.EqualTo(1));
            Assert.That(results[0].Editions, Has.Count.EqualTo(2));
        }

        [Test]
        public void should_not_log_raw_query_or_exception_text_during_the_fallback()
        {
            var previousConfiguration = LogManager.Configuration;
            var memory = new MemoryTarget("metadata-search-fallback-memory")
            {
                Layout = "${level}|${message}|${exception:format=tostring}"
            };
            var configuration = new LoggingConfiguration();
            configuration.AddRule(LogLevel.Trace, LogLevel.Fatal, memory, typeof(BookInfoProxyMetadataSearchFallbackFixture).FullName);

            try
            {
                LogManager.Configuration = configuration;
                LogManager.ReconfigExistingLoggers();

                var rawQuery = "Native Book\r\npassword=topsecret";
                var proxy = CreateProxy(new TokenOnlyHardcoverMetadataProxy(), MetadataSearchException(HttpStatusCode.NotFound));
                proxy.SearchForNewBook(rawQuery, null, mediaType: BookMediaType.Audiobook);

                Assert.That(memory.Logs, Has.Some.Contains("trying Hardcover"));
                Assert.That(memory.Logs, Has.None.Contains("Native Book"));
                Assert.That(memory.Logs, Has.None.Contains("password=topsecret"));
                Assert.That(memory.Logs, Has.None.Contains("metadata search failed"));
                Assert.That(memory.Logs, Has.None.Contains("\r"));
                Assert.That(memory.Logs, Has.None.Contains("\n"));
            }
            finally
            {
                LogManager.Configuration = previousConfiguration;
                LogManager.ReconfigExistingLoggers();
            }
        }

        [Test]
        public void should_disable_url_logging_for_metadata_server_search_requests()
        {
            var configService = DispatchProxy.Create<IConfigService, ConfigServiceProxy>();
            var cached = new Mock<ICachedHttpResponseService>();
            HttpRequest capturedRequest = null;
            cached.Setup(service => service.Get<List<SearchJsonResource>>(
                    It.IsAny<HttpRequest>(),
                    false,
                    It.IsAny<TimeSpan>()))
                .Callback<HttpRequest, bool, TimeSpan>((request, _, _) => capturedRequest = request)
                .Returns<HttpRequest, bool, TimeSpan>((request, _, _) => new HttpResponse<List<SearchJsonResource>>(
                    new HttpResponse(request, new HttpHeader { ContentType = "application/json" }, "[]")));

            var proxy = new NzbDrone.Core.MetadataSource.Goodreads.GoodreadsSearchProxy(
                cached.Object,
                LogManager.GetCurrentClassLogger(),
                new MetadataRequestBuilder(configService));

            proxy.SearchMetadataApi("Native Book password=topsecret");

            Assert.That(capturedRequest, Is.Not.Null);
            Assert.That(capturedRequest.LogRequest, Is.False);
            Assert.That(capturedRequest.LogHttpError, Is.False);
        }

        [Test]
        public void should_disable_url_logging_for_legacy_goodreads_search_requests()
        {
            var cached = new Mock<ICachedHttpResponseService>();
            HttpRequest capturedRequest = null;
            cached.Setup(service => service.Get<List<SearchJsonResource>>(
                    It.IsAny<HttpRequest>(),
                    true,
                    It.IsAny<TimeSpan>(),
                    It.IsAny<Func<HttpResponse, bool>>()))
                .Callback<HttpRequest, bool, TimeSpan, Func<HttpResponse, bool>>((request, _, _, _) => capturedRequest = request)
                .Returns<HttpRequest, bool, TimeSpan, Func<HttpResponse, bool>>((request, _, _, _) => new HttpResponse<List<SearchJsonResource>>(
                    new HttpResponse(request, new HttpHeader { ContentType = "application/json" }, "[]")));

            var proxy = new NzbDrone.Core.MetadataSource.Goodreads.GoodreadsSearchProxy(
                cached.Object,
                LogManager.GetCurrentClassLogger());

            proxy.Search("Native Book password=topsecret");

            Assert.That(capturedRequest, Is.Not.Null);
            Assert.That(capturedRequest.LogRequest, Is.False);
            Assert.That(capturedRequest.LogHttpError, Is.False);
        }

        [Test]
        public async Task should_not_log_or_return_metadata_search_query_from_error_pipeline()
        {
            var previousConfiguration = LogManager.Configuration;
            var memory = new MemoryTarget("metadata-search-error-pipeline-memory")
            {
                Layout = "${level}|${message}|${exception:format=tostring}"
            };
            var configuration = new LoggingConfiguration();
            var logger = LogManager.GetLogger("metadata-search-error-pipeline-test");
            configuration.AddRule(LogLevel.Trace, LogLevel.Fatal, memory, logger.Name);

            try
            {
                LogManager.Configuration = configuration;
                LogManager.ReconfigExistingLoggers();

                var rawQuery = "Native Book\r\npassword=topsecret";
                var configService = DispatchProxy.Create<IConfigService, ConfigServiceProxy>();
                var cached = new Mock<ICachedHttpResponseService>();
                cached.Setup(service => service.Get<List<SearchJsonResource>>(
                        It.IsAny<HttpRequest>(),
                        false,
                        It.IsAny<TimeSpan>()))
                    .Returns<HttpRequest, bool, TimeSpan>((request, _, _) =>
                    {
                        var response = new HttpResponse(
                            request,
                            new HttpHeader(),
                            "metadata search failed",
                            HttpStatusCode.ServiceUnavailable);
                        throw new HttpException(request, response);
                    });

                var searchProxy = new NzbDrone.Core.MetadataSource.Goodreads.GoodreadsSearchProxy(
                    cached.Object,
                    logger,
                    new MetadataRequestBuilder(configService));
                var exception = Assert.Throws<GoodreadsException>(() => searchProxy.SearchMetadataApi(rawQuery));

                Assert.That(exception.UpstreamStatusCode, Is.EqualTo(HttpStatusCode.ServiceUnavailable));
                Assert.That(exception.InnerException, Is.Null);
                Assert.That(exception.ToString(), Does.Not.Contain("Native Book"));
                Assert.That(exception.ToString(), Does.Not.Contain("topsecret"));

                var context = new DefaultHttpContext();
                context.Request.Method = "GET";
                context.Request.Path = "/api/v1/book/lookup";
                context.Response.Body = new MemoryStream();
                context.Features.Set<IExceptionHandlerPathFeature>(new TestExceptionHandlerPathFeature(exception));
                await new ChaptarrErrorPipeline(logger).HandleException(context);

                context.Response.Body.Position = 0;
                using var reader = new StreamReader(context.Response.Body);
                var errorResponse = await reader.ReadToEndAsync();

                Assert.That(memory.Logs, Has.None.Contains("Native Book"));
                Assert.That(memory.Logs, Has.None.Contains("topsecret"));
                Assert.That(errorResponse, Does.Not.Contain("Native Book"));
                Assert.That(errorResponse, Does.Not.Contain("topsecret"));
            }
            finally
            {
                LogManager.Configuration = previousConfiguration;
                LogManager.ReconfigExistingLoggers();
            }
        }
    }
}

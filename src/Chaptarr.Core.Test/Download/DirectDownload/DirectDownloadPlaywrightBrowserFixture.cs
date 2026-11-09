using System;
using System.IO;
using Moq;
using NzbDrone.Common.EnvironmentInfo;
using NzbDrone.Common.Http;
using System.Threading.Tasks;
using NLog;
using NUnit.Framework;
using NzbDrone.Core.Download.Clients.Direct;

namespace Chaptarr.Core.Test.Download.DirectDownload
{
    [TestFixture]
    [Category("Playwright")]
    public class DirectDownloadPlaywrightBrowserFixture
    {
        [SetUp]
        public void RequireExplicitBrowserTestOptIn()
        {
            if (!string.Equals(Environment.GetEnvironmentVariable("DIRECT_DOWNLOAD_REQUIRE_PLAYWRIGHT"), "true", StringComparison.OrdinalIgnoreCase))
            {
                Assert.Ignore("Set DIRECT_DOWNLOAD_REQUIRE_PLAYWRIGHT=true to run the headless Chromium integration tests.");
            }
        }

        [Test]
        public async Task should_resolve_javascript_rendered_slow_link_with_headless_chromium()
        {
            const string html = """
                <!doctype html>
                <html>
                  <body>
                    <a href="/fast_download/fast-result">Fast download</a>
                    <script>
                      setTimeout(() => {
                        const link = document.createElement('a');
                        link.href = '/slow_download/slow-result?token=download-token';
                        link.textContent = 'Slow download';
                        document.body.appendChild(link);
                      }, 75);
                    </script>
                  </body>
                </html>
                """;

            var resolver = CreateResolver(html);

            await EnsureBrowserAvailableAsync(resolver);

            var resolvedUrl = await resolver.TryResolveSlowDownloadUrlAsync("https://pages.example.test/" + "md5/book-id?key=page-token").WaitAsync(TimeSpan.FromSeconds(30));

            Assert.That(resolvedUrl, Is.EqualTo("https://pages.example.test/" + "slow_download/slow-result?token=download-token"));
        }

        [Test]
        public async Task should_resolve_direct_epub_link_with_headless_chromium()
        {
            const string html = """
                <!doctype html>
                <html><body><a href="https://files.example.test/books/sample.epub">Download EPUB</a></body></html>
                """;

            var resolver = CreateResolver(html);

            await EnsureBrowserAvailableAsync(resolver);

            var resolvedUrl = await resolver.TryResolveSlowDownloadUrlAsync("https://pages.example.test/" + "md5/book-id").WaitAsync(TimeSpan.FromSeconds(30));

            Assert.That(resolvedUrl, Is.EqualTo("https://files.example.test/books/sample.epub"));
        }

        [Test]
        public async Task should_resolve_relative_book_file_link_with_headless_chromium()
        {
            const string html = """
                <!doctype html>
                <html><body><a href="/books/sample.epub?download=1">Download EPUB</a></body></html>
                """;

            var resolver = CreateResolver(html);

            await EnsureBrowserAvailableAsync(resolver);

            var resolvedUrl = await resolver.TryResolveSlowDownloadUrlAsync("https://pages.example.test/" + "md5/book-id").WaitAsync(TimeSpan.FromSeconds(30));

            Assert.That(resolvedUrl, Is.EqualTo("https://pages.example.test/" + "books/sample.epub?download=1"));
        }

        private static async Task EnsureBrowserAvailableAsync(PlaywrightBrowserResolver resolver)
        {
            if (await resolver.IsAvailableAsync().WaitAsync(TimeSpan.FromSeconds(30)))
            {
                return;
            }

            if (string.Equals(Environment.GetEnvironmentVariable("DIRECT_DOWNLOAD_REQUIRE_PLAYWRIGHT"), "true", StringComparison.OrdinalIgnoreCase))
            {
                Assert.Fail("Headless Chromium is required but could not be launched. " + resolver.LastLaunchFailure);
            }

            Assert.Ignore("Headless Chromium is not installed on this test host.");
        }

        private static PlaywrightBrowserResolver CreateResolver(string html)
        {
            var folders = new Mock<IAppFolderInfo>();
            folders.SetupGet(f => f.StartUpFolder).Returns(TestContext.CurrentContext.TestDirectory);
            folders.SetupGet(f => f.AppDataFolder).Returns(Path.Combine(TestContext.CurrentContext.TestDirectory, "app-config"));
            var http = new Mock<IHttpClient>(MockBehavior.Strict);
            http.Setup(h => h.ExecuteAsync(It.IsAny<HttpRequest>())).Returns((HttpRequest request) =>
            {
                Assert.That(request.AllowPrivateNetworkTargets, Is.False);
                Assert.That(request.AllowAutoRedirect, Is.False);
                Assert.That(request.MaxResponseBytes, Is.LessThanOrEqualTo(10 * 1024 * 1024));
                Assert.That(request.StoreRequestCookie || request.StoreResponseCookie, Is.False);
                var headers = new HttpHeader { ContentType = "text/html; charset=utf-8" };
                return Task.FromResult(new HttpResponse(request, headers, html));
            });
            return new PlaywrightBrowserResolver(LogManager.GetCurrentClassLogger(), http.Object, folders.Object);
        }
    }
}

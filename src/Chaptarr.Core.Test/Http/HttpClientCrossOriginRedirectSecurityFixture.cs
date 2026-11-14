using System.Net;
using System.Threading.Tasks;
using Chaptarr.Core.Test.Indexers;
using NLog;
using NLog.Config;
using NLog.Targets;
using NUnit.Framework;
using NzbDrone.Common.Http;
using NzbDrone.Core.Http.CloudFlare;

namespace Chaptarr.Core.Test.Http
{
    [TestFixture]
    [NonParallelizable]
    public class HttpClientCrossOriginRedirectSecurityFixture
    {
        private const string SourceUrl = "https://configured-service.example/api/resource";
        private const string RedirectUrl = "https://redirect-target.example/receive";

        [Test]
        public void should_not_forward_api_key_headers_to_another_origin()
        {
            var transport = CreateRedirectTransport();
            var request = CreateRequest();
            request.Headers.Add("X-Api-Key", "secret");

            var exception = Assert.ThrowsAsync<WebException>(async () => await transport.CreateClient().ExecuteAsync(request));

            Assert.That(exception.Status, Is.EqualTo(WebExceptionStatus.ProtocolError));
            Assert.That(transport.RequestedUrls, Is.EqualTo(new[] { SourceUrl }));
        }

        [Test]
        public void should_not_forward_credentials_to_another_origin()
        {
            var transport = CreateRedirectTransport();
            var request = CreateRequest();
            request.Credentials = new NetworkCredential("reader", "secret");

            Assert.ThrowsAsync<WebException>(async () => await transport.CreateClient().ExecuteAsync(request));

            Assert.That(transport.RequestedUrls, Is.EqualTo(new[] { SourceUrl }));
        }

        [Test]
        public void should_not_forward_cookies_to_another_origin()
        {
            var transport = CreateRedirectTransport();
            var request = CreateRequest();
            request.Cookies.Add("session", "secret");

            Assert.ThrowsAsync<WebException>(async () => await transport.CreateClient().ExecuteAsync(request));

            Assert.That(transport.RequestedUrls, Is.EqualTo(new[] { SourceUrl }));
        }

        [Test]
        public void should_not_forward_request_bodies_to_another_origin()
        {
            var transport = CreateRedirectTransport();
            var request = CreateRequest();
            request.SetContent("{\"password\":\"secret\"}");

            Assert.ThrowsAsync<WebException>(async () => await transport.CreateClient().ExecuteAsync(request));

            Assert.That(transport.RequestedUrls, Is.EqualTo(new[] { SourceUrl }));
        }

        [Test]
        public void should_not_send_redirect_destination_user_info_to_another_origin()
        {
            var transport = new DirectDownloadTestHttp();
            const string destinationUrl = "https://reader:secret@redirect-target.example/receive";
            transport.AddRoute(
                url => url == SourceUrl,
                request => Task.FromResult(BuildRedirectResponse(request, destinationUrl)));
            transport.AddRoute(
                url => url == destinationUrl,
                request => Task.FromResult(new HttpResponse(request, new HttpHeader(), new byte[0])));

            var exception = Assert.ThrowsAsync<WebException>(async () => await transport.CreateClient().ExecuteAsync(CreateRequest()));

            Assert.That(exception.Status, Is.EqualTo(WebExceptionStatus.ProtocolError));
            Assert.That(exception.Message, Does.Not.Contain("reader"));
            Assert.That(transport.RequestedUrls, Is.EqualTo(new[] { SourceUrl }));
        }

        [Test]
        public async Task should_follow_public_cross_origin_redirects_without_sensitive_request_data()
        {
            var transport = CreateRedirectTransport();

            var response = await transport.CreateClient().ExecuteAsync(CreateRequest());

            Assert.That(response.StatusCode, Is.EqualTo(HttpStatusCode.OK));
            Assert.That(transport.RequestedUrls, Is.EqualTo(new[] { SourceUrl, RedirectUrl }));
        }

        [Test]
        public async Task should_follow_cross_origin_redirects_with_unrelated_custom_headers()
        {
            var transport = CreateRedirectTransport();
            var request = CreateRequest();
            request.Headers.Add("X-Request-Trace", "trace-id");

            var response = await transport.CreateClient().ExecuteAsync(request);

            Assert.That(response.StatusCode, Is.EqualTo(HttpStatusCode.OK));
            Assert.That(transport.RequestedUrls, Is.EqualTo(new[] { SourceUrl, RedirectUrl }));
        }

        [Test]
        public async Task should_follow_same_origin_redirects_with_sensitive_request_data()
        {
            var transport = new DirectDownloadTestHttp();
            transport.AddRoute(
                url => url == SourceUrl,
                request => Task.FromResult(BuildRedirectResponse(request, "https://configured-service.example/receive")));
            transport.AddRoute(
                url => url == "https://configured-service.example/receive",
                request => Task.FromResult(new HttpResponse(request, new HttpHeader(), new byte[0])));
            var request = CreateRequest();
            request.Headers.Add("X-Api-Key", "secret");

            var response = await transport.CreateClient().ExecuteAsync(request);

            Assert.That(response.StatusCode, Is.EqualTo(HttpStatusCode.OK));
            Assert.That(transport.RequestedUrls, Is.EqualTo(new[]
            {
                SourceUrl,
                "https://configured-service.example/receive"
            }));
        }

        [Test]
        public void should_not_log_request_query_when_request_logging_is_disabled()
        {
            var previousConfiguration = LogManager.Configuration;
            var memory = new MemoryTarget("http-request-query-redaction")
            {
                Layout = "${level}|${message}|${exception:format=tostring}"
            };
            var configuration = new LoggingConfiguration();
            var logger = LogManager.GetLogger("http-query-redaction-test");
            configuration.AddRule(LogLevel.Trace, LogLevel.Fatal, memory, logger.Name);

            try
            {
                LogManager.Configuration = configuration;
                LogManager.ReconfigExistingLoggers();

                const string url = "https://configured-service.example/api/v5/search?q=Native%20Book%0D%0Apassword%3Dtopsecret";
                var transport = new DirectDownloadTestHttp();
                transport.AddRoute(
                    requestedUrl => requestedUrl == url,
                    request => Task.FromResult(new HttpResponse(
                        request,
                        new HttpHeader(),
                        "not found Native%20Book%0D%0Apassword%3Dtopsecret",
                        HttpStatusCode.NotFound)));

                var request = new HttpRequest(url)
                {
                    AllowAutoRedirect = false,
                    LogHttpError = false,
                    LogRequest = false
                };

                Assert.ThrowsAsync<HttpException>(async () => await transport.CreateClient(logger).ExecuteAsync(request));

                Assert.That(memory.Logs, Has.None.Contains("Native%20Book"));
                Assert.That(memory.Logs, Has.None.Contains("%3Dtopsecret"));
                Assert.That(memory.Logs, Has.None.Contains("password=topsecret"));
            }
            finally
            {
                LogManager.Configuration = previousConfiguration;
                LogManager.ReconfigExistingLoggers();
            }
        }

        [Test]
        public void should_not_log_request_query_from_cloudflare_interceptor_when_request_logging_is_disabled()
        {
            var previousConfiguration = LogManager.Configuration;
            var memory = new MemoryTarget("cloudflare-request-query-redaction")
            {
                Layout = "${level}|${message}|${exception:format=tostring}"
            };
            var configuration = new LoggingConfiguration();
            var logger = LogManager.GetLogger("cloudflare-query-redaction-test");
            configuration.AddRule(LogLevel.Trace, LogLevel.Fatal, memory, logger.Name);

            try
            {
                LogManager.Configuration = configuration;
                LogManager.ReconfigExistingLoggers();

                const string url = "https://configured-service.example/api/v5/search?q=Native%20Book%0D%0Apassword%3Dtopsecret";
                var request = new HttpRequest(url)
                {
                    LogRequest = false
                };
                var response = new HttpResponse(
                    request,
                    new HttpHeader(),
                    "challenge page with cdn-cgi/scripts/cf.challenge.js",
                    HttpStatusCode.Forbidden);

                Assert.Throws<CloudFlareCaptchaException>(() => new CloudFlareHttpInterceptor(logger).PostResponse(response));

                Assert.That(memory.Logs, Has.None.Contains("Native%20Book"));
                Assert.That(memory.Logs, Has.None.Contains("%3Dtopsecret"));
                Assert.That(memory.Logs, Has.None.Contains("password=topsecret"));
            }
            finally
            {
                LogManager.Configuration = previousConfiguration;
                LogManager.ReconfigExistingLoggers();
            }
        }

        private static DirectDownloadTestHttp CreateRedirectTransport()
        {
            var transport = new DirectDownloadTestHttp();
            transport.AddRoute(
                url => url == SourceUrl,
                request => Task.FromResult(BuildRedirectResponse(request, RedirectUrl)));
            transport.AddRoute(
                url => url == RedirectUrl,
                request => Task.FromResult(new HttpResponse(request, new HttpHeader(), new byte[0])));
            return transport;
        }

        private static HttpRequest CreateRequest()
        {
            return new HttpRequest(SourceUrl)
            {
                AllowAutoRedirect = true
            };
        }

        private static HttpResponse BuildRedirectResponse(HttpRequest request, string destinationUrl)
        {
            var headers = new HttpHeader
            {
                { "Location", destinationUrl }
            };
            return new HttpResponse(request, headers, new byte[0], HttpStatusCode.TemporaryRedirect);
        }
    }
}

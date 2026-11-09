using System;
using System.Net.Http;
using System.Threading.Tasks;
using Moq;
using NLog;
using NUnit.Framework;
using NzbDrone.Common.Http;
using NzbDrone.Common.Http.Dispatchers;
using NzbDrone.Common.Http.Proxy;

namespace Chaptarr.Core.Test.Http
{
    [TestFixture]
    public class PublicSocketPolicyFixture
    {
        [TestCase("127.0.0.1")]
        [TestCase("localhost")]
        [TestCase("[::1]")]
        [TestCase("169.254.169.254")]
        public async Task public_fetch_policy_rejects_private_addresses_at_socket_connection(string host)
        {
            var factory = new ManagedSocketsHttpHandlerFactory(new Mock<ICreateManagedWebProxy>().Object,
                new Mock<ICertificateValidationService>().Object, LogManager.GetCurrentClassLogger());
            using var handler = factory.CreateHandler(null, false, false, null, false, 1, allowPrivateNetworkTargets: false);
            Assert.That(handler.UseProxy, Is.False, "Environment proxies must not resolve an unchecked destination.");
            using var client = new System.Net.Http.HttpClient(handler) { Timeout = TimeSpan.FromSeconds(5) };
            var error = Assert.ThrowsAsync<HttpRequestException>(async () => await client.GetAsync("http://" + host + ":9/"));
            Assert.That(error.ToString(), Does.Contain("private or reserved").Or.Contain("disallowed address"));
            await Task.CompletedTask;
        }
    }
}

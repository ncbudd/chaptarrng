using System;
using System.IO;
using System.Linq;
using System.Net;
using System.Security.Cryptography;
using System.Security.Claims;
using System.Collections.Generic;
using Microsoft.AspNetCore.Authorization;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using NzbDrone.Host;
using System.Threading;
using System.Threading.Tasks;
using NzbDrone.Common.Cache;
using NzbDrone.Common.Disk;
using Chaptarr.Http.Authentication;
using Microsoft.AspNetCore.Http;
using Moq;
using NUnit.Framework;
using NzbDrone.Common.EnvironmentInfo;
using NzbDrone.Core.Authentication;
using NzbDrone.Core.Configuration;

namespace Chaptarr.Core.Test.Authentication
{
    [TestFixture]
    public class AuditAuthenticationFixture
    {
        [TestCase(false, true)]
        [TestCase(true, false)]
        public async Task local_authentication_bypass_cannot_open_a_misconfigured_identity_provider(bool misconfigured, bool allowed)
        {
            var config = new Mock<IConfigFileProvider>();
            config.SetupGet(c => c.AuthenticationRequired).Returns(AuthenticationRequiredType.DisabledForLocalAddresses);
            config.SetupGet(c => c.AuthenticationMethodIsMisconfigured).Returns(misconfigured);
            var setup = new Mock<IInitialSetupTokenService>();
            setup.SetupGet(s => s.IsRequired).Returns(false);
            using var services = new ServiceCollection().AddSingleton(setup.Object).BuildServiceProvider();
            var http = new DefaultHttpContext { RequestServices = services };
            http.Connection.RemoteIpAddress = IPAddress.Loopback;
            var requirement = new NzbDrone.Http.Authentication.BypassableDenyAnonymousAuthorizationRequirement();
            var authorization = new AuthorizationHandlerContext(new[] { requirement }, new ClaimsPrincipal(), http);
            await new NzbDrone.Http.Authentication.UiAuthorizationHandler(config.Object).HandleAsync(authorization);
            Assert.That(authorization.HasSucceeded, Is.EqualTo(allowed));
        }

        [Test]
        public void browser_token_requires_cookie_and_is_revoked_on_logout_and_security_change()
        {
            var stamp = "first";
            var config = new Mock<IConfigFileProvider>();
            config.SetupGet(c => c.AuthCookieStamp).Returns(() => stamp);
            var tokens = new UiSessionTokenService(config.Object);
            var browser = new DefaultHttpContext();
            var token = tokens.Issue(browser);
            var cookie = browser.Response.Headers.SetCookie.ToString().Split(';')[0];
            var attacker = new DefaultHttpContext();
            Assert.That(tokens.Validate(attacker, token), Is.False);
            browser.Request.Headers.Cookie = cookie;
            Assert.That(tokens.Validate(browser, token), Is.True);
            tokens.Revoke(browser);
            Assert.That(tokens.Validate(browser, token), Is.False);
            token = tokens.Issue(browser);
            browser.Request.Headers.Cookie = browser.Response.Headers.SetCookie.ToArray()[^1].Split(';')[0];
            stamp = "changed";
            Assert.That(tokens.Validate(browser, token), Is.False);
        }

        [Test]
        public void setup_token_is_private_random_and_stops_authenticating_after_account_creation()
        {
            var path = Path.Combine(Path.GetTempPath(), "chaptarr-setup-test-" + Guid.NewGuid());
            Directory.CreateDirectory(path);
            try
            {
                var users = new Mock<IUserService>();
                var folders = new Mock<IAppFolderInfo>();
                folders.SetupGet(f => f.AppDataFolder).Returns(path);
                var config = new Mock<IConfigFileProvider>();
                config.SetupGet(c => c.AuthenticationMethod).Returns(AuthenticationType.Forms);
                var service = new InitialSetupTokenService(users.Object, config.Object, folders.Object);
                service.EnsureToken();
                var token = File.ReadAllText(service.TokenPath);
                Assert.That(token.Length, Is.EqualTo(64));
                Assert.That(service.Validate(token), Is.True);
                Assert.That(service.Validate(new string('0', 64)), Is.False);
                if (!OperatingSystem.IsWindows())
                {
                    Assert.That(File.GetUnixFileMode(service.TokenPath), Is.EqualTo(UnixFileMode.UserRead | UnixFileMode.UserWrite));
                }

                users.Setup(u => u.FindUser()).Returns(new User());
                Assert.That(service.Validate(token), Is.False);
                service.EnsureToken();
                Assert.That(File.Exists(service.TokenPath), Is.False);
            }
            finally { Directory.Delete(path, true); }
        }

        [Test]
        public void parallel_failed_logins_cannot_bypass_the_hashing_budget()
        {
            var config = new Mock<IConfigFileProvider>();
            config.SetupGet(c => c.AuthenticationMethod).Returns(AuthenticationType.Forms);
            var users = new Mock<IUserService>();
            var calls = 0;
            users.Setup(u => u.FindUser("owner", "wrong")).Returns(() =>
            {
                Interlocked.Increment(ref calls);
                return null;
            });
            var auth = new AuthenticationService(config.Object, users.Object, new CacheManager());
            Parallel.For(0, 100, _ =>
            {
                var context = new DefaultHttpContext();
                context.Connection.RemoteIpAddress = IPAddress.Parse("198.51.100.99");
                Assert.That(auth.Login(context.Request, "owner", "wrong"), Is.Null);
            });
            Assert.That(calls, Is.EqualTo(10));
        }

        [Test]
        public void successful_legacy_login_upgrades_the_password_hash_without_changing_identity()
        {
            var salt = RandomNumberGenerator.GetBytes(16);
            var user = new User
            {
                Id = 17, Identifier = Guid.NewGuid(), Username = "owner", Iterations = 10000,
                Salt = Convert.ToBase64String(salt),
                Password = Convert.ToBase64String(Rfc2898DeriveBytes.Pbkdf2("correct", salt, 10000, HashAlgorithmName.SHA512, 32))
            };
            var originalIdentifier = user.Identifier;
            var repository = new Mock<IUserRepository>();
            repository.Setup(r => r.FindUser("owner")).Returns(user);
            repository.Setup(r => r.Update(It.IsAny<User>())).Returns((User updated) => updated);
            var service = new UserService(repository.Object, new Mock<IAppFolderInfo>().Object, new Mock<IDiskProvider>().Object);
            Assert.That(service.FindUser("owner", "wrong"), Is.Null);
            Assert.That(user.Iterations, Is.EqualTo(10000));
            var authenticated = service.FindUser("owner", "correct");
            Assert.That(authenticated.Identifier, Is.EqualTo(originalIdentifier));
            Assert.That(authenticated.Iterations, Is.EqualTo(UserService.Iterations));
            Assert.That(service.FindUser("owner", "correct"), Is.SameAs(authenticated));
            repository.Verify(r => r.Update(It.IsAny<User>()), Times.Once);
        }

        [TestCase("full", true, true)]
        [TestCase("seerr", true, false)]
        [TestCase("full", false, false)]
        public async Task administrative_media_move_policy_is_registered_and_requires_full_authenticated_scope(string scope, bool authenticated, bool allowed)
        {
            var configuration = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string>
            {
                ["dataProtectionFolder"] = Path.GetTempPath()
            }).Build();
            var services = new ServiceCollection();
            services.AddSingleton(new Mock<IConfigFileProvider>().Object);
            new Startup(configuration).ConfigureServices(services);
            using var provider = services.BuildServiceProvider();
            var policy = await provider.GetRequiredService<IAuthorizationPolicyProvider>().GetPolicyAsync("AdminApiKey");
            Assert.That(policy, Is.Not.Null);
            var identity = new ClaimsIdentity(new[] { new Claim("ApiKeyScope", scope) }, authenticated ? "test" : null);
            var result = await provider.GetRequiredService<IAuthorizationService>().AuthorizeAsync(new ClaimsPrincipal(identity), null, policy);
            Assert.That(result.Succeeded, Is.EqualTo(allowed));
        }

        [TestCase(AuthenticationType.External)]
        [TestCase(AuthenticationType.Oidc)]
        [TestCase(AuthenticationType.Plex)]
        public void external_identity_providers_do_not_become_anonymous_during_first_run(AuthenticationType method)
        {
            var config = new Mock<IConfigFileProvider>();
            config.SetupGet(c => c.AuthenticationMethod).Returns(method);
            var folders = new Mock<IAppFolderInfo>();
            folders.SetupGet(f => f.AppDataFolder).Returns(Path.GetTempPath());
            var service = new InitialSetupTokenService(new Mock<IUserService>().Object, config.Object, folders.Object);
            Assert.That(service.IsRequired, Is.False);
        }
    }
}

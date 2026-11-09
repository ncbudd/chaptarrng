using System;
using System.Linq;
using Chaptarr.Http.Extensions;
using Microsoft.AspNetCore.Http;
using NLog;
using NzbDrone.Common.Cache;
using NzbDrone.Common.Extensions;
using NzbDrone.Core.Authentication;
using NzbDrone.Core.Configuration;
using NzbDrone.Common.Instrumentation;

namespace Chaptarr.Http.Authentication
{
    public interface IAuthenticationService
    {
        void LogUnauthorized(HttpRequest context);
        User Login(HttpRequest request, string username, string password);
        void Logout(HttpContext context);
    }

    public class AuthenticationService : IAuthenticationService
    {
        private static readonly Logger _authLogger = LogManager.GetLogger("Auth");
        private const int MaxFailedAttemptsPerIp = 10;
        private static readonly TimeSpan FailedAttemptWindow = TimeSpan.FromMinutes(15);
        private static readonly object[] AttemptLocks = Enumerable.Range(0, 128).Select(_ => new object()).ToArray();

        private readonly IConfigFileProvider _configFileProvider;
        private readonly IUserService _userService;
        private readonly ICached<int> _failedAttemptsByIp;

        public AuthenticationService(IConfigFileProvider configFileProvider, IUserService userService, ICacheManager cacheManager)
        {
            _configFileProvider = configFileProvider;
            _userService = userService;
            _failedAttemptsByIp = cacheManager.GetRollingCache<int>(GetType(), "failedLoginAttemptsByIp", FailedAttemptWindow);
        }

        public User Login(HttpRequest request, string username, string password)
        {
            var method = _configFileProvider.AuthenticationMethod;
            if (method == AuthenticationType.None || method == AuthenticationType.External)
            {
                return null;
            }

            // When Plex/OIDC is the configured primary auth, only allow local fallback to prevent
            // remote credential-based bypass of external auth (recovery is still possible from LAN).
            var isLocalCredentials = method == AuthenticationType.Basic || method == AuthenticationType.Forms;
            if (!isLocalCredentials && !TrustedNetworkPolicy.IsLocalOrTrusted(request, _configFileProvider))
            {
                return null;
            }

            var remoteIp = request.GetRemoteIP();
            var attemptLock = AttemptLocks[(StringComparer.Ordinal.GetHashCode(remoteIp ?? string.Empty) & int.MaxValue) % AttemptLocks.Length];
            lock (attemptLock)
            {
                var failures = _failedAttemptsByIp.Find(remoteIp);
                if (failures >= MaxFailedAttemptsPerIp)
                {
                    LogInvalidated(request);
                    return null;
                }

                // Reserve the attempt before expensive verification. Concurrent failures cannot
                // overwrite one another, and distinct addresses do not serialize hashing.
                _failedAttemptsByIp.Set(remoteIp, failures + 1, FailedAttemptWindow);
            }

            var user = _userService.FindUser(username, password);

            if (user != null)
            {
                lock (attemptLock)
                {
                    _failedAttemptsByIp.Remove(remoteIp);
                }
                LogSuccess(request, username);

                return user;
            }

            LogFailure(request, username);

            return null;
        }

        public void Logout(HttpContext context)
        {
            var method = _configFileProvider.AuthenticationMethod;
            if (method == AuthenticationType.None)
            {
                return;
            }

            if (context.User != null)
            {
                LogLogout(context.Request, context.User.Identity.Name);
            }
        }

        public void LogUnauthorized(HttpRequest context)
        {
            _authLogger.InfoSafe("Auth-Unauthorized ip {0} url '{1}'", context.GetRemoteIP(), context.Path);
        }

        private void LogInvalidated(HttpRequest context)
        {
            _authLogger.Info("Auth-Invalidated ip {0}", context.GetRemoteIP());
        }

        private void LogFailure(HttpRequest context, string username)
        {
            _authLogger.WarnSafe("Auth-Failure ip {0} username '{1}'", context.GetRemoteIP(), username);
        }

        private void LogSuccess(HttpRequest context, string username)
        {
            _authLogger.InfoSafe("Auth-Success ip {0} username '{1}'", context.GetRemoteIP(), username);
        }

        private void LogLogout(HttpRequest context, string username)
        {
            _authLogger.Info("Auth-Logout ip {0} username '{1}'", context.GetRemoteIP(), username);
        }

    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Http;
using NzbDrone.Core.Configuration;

namespace Chaptarr.Http.Authentication
{
    public interface IUiSessionTokenService
    {
        string Issue(HttpContext context);
        bool Validate(HttpContext context, string token);
        void Revoke(HttpContext context);
    }

    // Interface registration is a singleton in the application's automatic DI scan;
    // concrete registrations are transient and must not own this cross-request state.
    // A JS token alone never authenticates an API call.
    public class UiSessionTokenService : IUiSessionTokenService
    {
        private const string CookieName = "ChaptarrUiSession";
        private readonly Dictionary<string, Session> _sessions = new Dictionary<string, Session>(StringComparer.Ordinal);
        private readonly IConfigFileProvider _config;
        private readonly object _sync = new object();

        public UiSessionTokenService(IConfigFileProvider config)
        {
            _config = config;
        }

        public string Issue(HttpContext context)
        {
            lock (_sync)
            {
                var now = DateTimeOffset.UtcNow;
                foreach (var key in _sessions.Where(p => p.Value.Expires <= now || p.Value.Stamp != _config.AuthCookieStamp).Select(p => p.Key).ToList())
                {
                    _sessions.Remove(key);
                }

                var id = context.Request.Cookies[CookieName];
                if (id == null || !_sessions.TryGetValue(id, out var session))
                {
                    if (_sessions.Count >= 10000)
                    {
                        throw new InvalidOperationException("Too many active browser sessions.");
                    }

                    id = Convert.ToHexString(RandomNumberGenerator.GetBytes(32));
                    session = new Session { Token = "ui_" + Convert.ToHexString(RandomNumberGenerator.GetBytes(32)), Stamp = _config.AuthCookieStamp };
                    _sessions.Add(id, session);
                }

                session.Expires = now.AddMinutes(30);
                context.Response.Cookies.Append(CookieName, id, CookieOptions(context.Request.IsHttps));
                return session.Token;
            }
        }

        public bool Validate(HttpContext context, string token)
        {
            var id = context.Request.Cookies[CookieName];
            if (id == null || token == null || token.Length != 67)
            {
                return false;
            }

            lock (_sync)
            {
                return _sessions.TryGetValue(id, out var session) && session.Expires > DateTimeOffset.UtcNow &&
                       session.Stamp == _config.AuthCookieStamp && CryptographicOperations.FixedTimeEquals(
                           Encoding.ASCII.GetBytes(session.Token), Encoding.ASCII.GetBytes(token));
            }
        }

        public void Revoke(HttpContext context)
        {
            lock (_sync)
            {
                var id = context.Request.Cookies[CookieName];
                if (id != null)
                {
                    _sessions.Remove(id);
                }

                context.Response.Cookies.Delete(CookieName, CookieOptions(context.Request.IsHttps));
            }
        }

        private CookieOptions CookieOptions(bool secure) => new CookieOptions
        {
            HttpOnly = true, Secure = secure, SameSite = SameSiteMode.Strict,
            Path = string.IsNullOrEmpty(_config.UrlBase) ? "/" : _config.UrlBase + "/", IsEssential = true
        };

        private sealed class Session
        {
            public string Token { get; set; }
            public string Stamp { get; set; }
            public DateTimeOffset Expires { get; set; }
        }
    }
}

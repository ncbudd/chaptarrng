using System;
using System.Collections.Generic;
using System.Security.Claims;
using System.Text;
using System.Text.Encodings.Web;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using NzbDrone.Core.Authentication;

namespace Chaptarr.Http.Authentication
{
    public class InitialSetupAuthenticationHandler : AuthenticationHandler<AuthenticationSchemeOptions>
    {
        public const string SchemeName = "InitialSetup";
        internal const string CookieSchemeName = "InitialSetupCookie";
        private readonly IInitialSetupTokenService _tokens;

        public InitialSetupAuthenticationHandler(IOptionsMonitor<AuthenticationSchemeOptions> options, ILoggerFactory logger,
            UrlEncoder encoder, IInitialSetupTokenService tokens)
            : base(options, logger, encoder)
        {
            _tokens = tokens;
        }

        internal static ClaimsPrincipal CreatePrincipal(string stamp = null)
        {
            var claims = new List<Claim> { new Claim("user", "setup"), new Claim("AuthType", SchemeName) };
            if (stamp != null)
            {
                claims.Add(new Claim(AuthenticationBuilderExtensions.AuthStampClaim, stamp));
            }

            return new ClaimsPrincipal(new ClaimsIdentity(claims, SchemeName, "user", "identifier"));
        }

        protected override Task<AuthenticateResult> HandleAuthenticateAsync()
        {
            if (!_tokens.IsRequired)
            {
                return Task.FromResult(AuthenticateResult.NoResult());
            }

            var authorization = Request.Headers.Authorization.ToString();
            if (!authorization.StartsWith("Basic ", StringComparison.OrdinalIgnoreCase))
            {
                return Context.AuthenticateAsync(CookieSchemeName);
            }

            if (authorization.Length > 256)
            {
                return Task.FromResult(AuthenticateResult.Fail("Invalid setup credentials."));
            }

            try
            {
                var credentials = Encoding.UTF8.GetString(Convert.FromBase64String(authorization.Substring(6))).Split(':', 2);
                if (credentials.Length == 2 && credentials[0] == "setup" && _tokens.Validate(credentials[1]))
                {
                    return Task.FromResult(AuthenticateResult.Success(new AuthenticationTicket(CreatePrincipal(), SchemeName)));
                }
            }
            catch (FormatException)
            {
                return Task.FromResult(AuthenticateResult.Fail("Invalid setup credentials."));
            }

            return Task.FromResult(AuthenticateResult.Fail("Invalid setup credentials."));
        }

        protected override Task HandleChallengeAsync(AuthenticationProperties properties)
        {
            if (HttpMethods.IsGet(Request.Method) && Context.GetEndpoint()?.Metadata.GetMetadata<AllowCookieRedirectAttribute>() != null)
            {
                Response.Redirect(Request.PathBase.Add(new PathString("/login")));
            }
            else
            {
                Response.StatusCode = StatusCodes.Status401Unauthorized;
            }

            return Task.CompletedTask;
        }
    }
}

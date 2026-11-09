using System;
using System.Security.Claims;
using System.Text;
using System.Text.Encodings.Web;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using NzbDrone.Core.Authentication;

namespace Chaptarr.Http.Authentication
{
    public class InitialSetupAuthenticationHandler : AuthenticationHandler<AuthenticationSchemeOptions>
    {
        public const string SchemeName = "InitialSetup";
        private readonly IInitialSetupTokenService _tokens;

        public InitialSetupAuthenticationHandler(IOptionsMonitor<AuthenticationSchemeOptions> options, ILoggerFactory logger,
            UrlEncoder encoder, IInitialSetupTokenService tokens)
            : base(options, logger, encoder)
        {
            _tokens = tokens;
        }

        protected override Task<AuthenticateResult> HandleAuthenticateAsync()
        {
            var authorization = Request.Headers.Authorization.ToString();
            if (!_tokens.IsRequired || !authorization.StartsWith("Basic ", StringComparison.OrdinalIgnoreCase) || authorization.Length > 256)
            {
                return Task.FromResult(AuthenticateResult.NoResult());
            }

            try
            {
                var credentials = Encoding.UTF8.GetString(Convert.FromBase64String(authorization.Substring(6))).Split(':', 2);
                if (credentials.Length == 2 && credentials[0] == "setup" && _tokens.Validate(credentials[1]))
                {
                    var identity = new ClaimsIdentity(new[] { new Claim("user", "setup"), new Claim("AuthType", SchemeName) }, SchemeName, "user", "identifier");
                    return Task.FromResult(AuthenticateResult.Success(new AuthenticationTicket(new ClaimsPrincipal(identity), SchemeName)));
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
            Response.StatusCode = 401;
            Response.Headers.WWWAuthenticate = "Basic realm=\"Chaptarr setup: username setup, password from setup-token in the config directory\"";
            return Task.CompletedTask;
        }
    }
}

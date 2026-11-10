using System;
using NLog;
using NzbDrone.Core.Authentication;
using NzbDrone.Core.Configuration;

namespace NzbDrone.Host
{
    public class FirstRunAuthenticationSetup
    {
        private readonly IConfigFileProvider _configFileProvider;
        private readonly Lazy<IUserService> _userService;
        private readonly Logger _logger;
        private readonly IInitialSetupTokenService _setupTokens;

        public FirstRunAuthenticationSetup(IConfigFileProvider configFileProvider, Lazy<IUserService> userService, Logger logger, IInitialSetupTokenService setupTokens = null)
        {
            _configFileProvider = configFileProvider;
            _userService = userService;
            _logger = logger;
            _setupTokens = setupTokens;
        }

        public void EnsureInitialAccountSetup()
        {
            _setupTokens?.EnsureToken();
            // Preserve external/OIDC/Plex authentication. Local first-run setup is protected by
            // InitialSetupAuthenticationHandler, which requires the owner-only setup-token file.
            if (!_configFileProvider.AuthenticationMethodIsMisconfigured &&
                _configFileProvider.AuthenticationMethod != AuthenticationType.External &&
                _configFileProvider.AuthenticationMethod != AuthenticationType.Oidc &&
                _configFileProvider.AuthenticationMethod != AuthenticationType.Plex && _userService.Value.FindUser() == null)
            {
                _logger.Info("Open the ChaptarrNG web UI and enter the token from the config directory's setup-token file to begin account setup.");
            }
        }
    }
}

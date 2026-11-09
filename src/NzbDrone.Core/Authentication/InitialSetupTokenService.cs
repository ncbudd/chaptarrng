using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using NzbDrone.Common.EnvironmentInfo;
using NzbDrone.Core.Configuration;

namespace NzbDrone.Core.Authentication
{
    public interface IInitialSetupTokenService
    {
        bool IsRequired { get; }
        string TokenPath { get; }
        void EnsureToken();
        bool Validate(string token);
    }

    public class InitialSetupTokenService : IInitialSetupTokenService
    {
        private readonly IUserService _users;
        private readonly IConfigFileProvider _config;
        private readonly object _sync = new object();

        public InitialSetupTokenService(IUserService users, IConfigFileProvider config, IAppFolderInfo folders)
        {
            _users = users;
            _config = config;
            TokenPath = Path.Combine(folders.AppDataFolder, "setup-token");
        }

        public string TokenPath { get; }

        public bool IsRequired => !_config.AuthenticationMethodIsMisconfigured &&
                                 (_config.AuthenticationMethod == AuthenticationType.None ||
                                   _config.AuthenticationMethod == AuthenticationType.Forms ||
                                   _config.AuthenticationMethod == AuthenticationType.Basic) && _users.FindUser() == null;

        public void EnsureToken()
        {
            lock (_sync)
            {
                if (!IsRequired)
                {
                    File.Delete(TokenPath);
                    return;
                }

                if (new FileInfo(TokenPath).LinkTarget != null)
                {
                    throw new IOException("The initial setup token must not be a symbolic link.");
                }

                if (File.Exists(TokenPath))
                {
                    if (new FileInfo(TokenPath).Length != 64)
                    {
                        throw new IOException("Invalid initial setup token file. Remove it and restart to generate a new token.");
                    }

                    if (!OperatingSystem.IsWindows())
                    {
                        File.SetUnixFileMode(TokenPath, UnixFileMode.UserRead | UnixFileMode.UserWrite);
                    }

                    return;
                }

                var options = new FileStreamOptions { Mode = FileMode.CreateNew, Access = FileAccess.Write, Share = FileShare.None };
                if (!OperatingSystem.IsWindows())
                {
                    options.UnixCreateMode = UnixFileMode.UserRead | UnixFileMode.UserWrite;
                }

                using var file = new FileStream(TokenPath, options);
                file.Write(Encoding.ASCII.GetBytes(Convert.ToHexString(RandomNumberGenerator.GetBytes(32))));
                file.Flush(true);
            }
        }

        public bool Validate(string token)
        {
            if (!IsRequired || token == null || token.Length != 64)
            {
                return false;
            }

            lock (_sync)
            {
                EnsureToken();
                var expected = File.ReadAllBytes(TokenPath);
                return CryptographicOperations.FixedTimeEquals(expected, Encoding.ASCII.GetBytes(token));
            }
        }
    }
}

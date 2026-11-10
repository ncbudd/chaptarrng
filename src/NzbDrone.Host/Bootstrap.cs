using System;
using System.Collections.Generic;
using Microsoft.Data.Sqlite;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using DryIoc;
using DryIoc.Microsoft.DependencyInjection;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Hosting.WindowsServices;
using Microsoft.Extensions.Logging;
using NLog;
using NLog.Extensions.Logging;
using Npgsql;
using PdfSharp;
using NzbDrone.Common.Composition.Extensions;
using NzbDrone.Common.Disk;
using NzbDrone.Common.EnvironmentInfo;
using NzbDrone.Common.Exceptions;
using NzbDrone.Common.Extensions;
using NzbDrone.Common.Instrumentation;
using NzbDrone.Common.Instrumentation.Extensions;
using NzbDrone.Common.Options;
using NzbDrone.Core.Configuration;
using NzbDrone.Core.Datastore;
using NzbDrone.Core.Datastore.Extensions;
using NzbDrone.Core.Http;
using NzbDrone.Core.Lifecycle;
using NzbDrone.Core.Messaging.Events;
using NzbDrone.Core.RemotePathMappings;
using NzbDrone.Core.Update;
// using NzbDrone.Core.MetadataSource.Hardcover; // Removed - using V5 API via BookInfoProxy
using NzbDrone.Core.Books.Services;
using NzbDrone.Core.Organizer;
using PostgresOptions = NzbDrone.Core.Datastore.PostgresOptions;

namespace NzbDrone.Host
{
    public static class Bootstrap
    {
        private static readonly Logger Logger = NzbDroneLogger.GetLogger(typeof(Bootstrap));

        public static readonly List<string> ASSEMBLIES = new List<string>
        {
            "Chaptarr.Host",
            "Chaptarr.Core",
            "Chaptarr.SignalR",
            "Chaptarr.Api.V1",
            "Chaptarr.Http"
        };

        // RegisterMany scans nested implementation types, including the private
        // DirectDownloadClient.NoopRemotePathMappingService used only as a local
        // constructor fallback. When it wins DI resolution, mapping APIs silently
        // return defaults (issue #199). Bind the real persistence-backed service
        // explicitly, after assembly scanning, for both interactive and utility hosts.
        internal static void RegisterRealRemotePathMappingService(IContainer container)
        {
            container.Register<IRemotePathMappingService, RemotePathMappingService>(
                Reuse.Singleton, ifAlreadyRegistered: IfAlreadyRegistered.Replace);
        }

        internal static void RegisterUpdatePackageProviders(IContainer container)
        {
            container.Register<IGitHubUpdatePackageProvider, GitHubUpdatePackageProvider>(
                Reuse.Singleton, ifAlreadyRegistered: IfAlreadyRegistered.Replace);
            container.Register<IUpdatePackageProvider, UpdatePackageProvider>(
                Reuse.Singleton, ifAlreadyRegistered: IfAlreadyRegistered.Replace);
        }

        public static void Start(string[] args, Action<IHostBuilder> trayCallback = null)
        {
            var restoreAttempted = false;
            var restoreCommitted = false;
            var previousDatabaseExisted = false;
            IAppFolderInfo restoredFolders = null;

            try
            {
                StartAttempt(args, trayCallback,
                    (folders, hadDatabase) =>
                    {
                        restoreAttempted = true;
                        previousDatabaseExisted = hadDatabase;
                        restoredFolders = folders;
                    },
                    () => restoreCommitted = true);
            }
            catch (Exception ex) when (restoreAttempted && !restoreCommitted && previousDatabaseExisted &&
                                       restoredFolders != null &&
                                       !FullRestoreBundle.HasIncompleteRestore(restoredFolders) &&
                                       File.Exists(restoredFolders.GetDatabase()))
            {
                Logger.Error(ex, "Backup restore failed during startup. The previous database and configuration were restored; starting ChaptarrNG with the previous data.");
                SqliteConnection.ClearAllPools();
                StartAttempt(args, trayCallback, null, null);
            }
        }

        private static void StartAttempt(string[] args, Action<IHostBuilder> trayCallback,
                                         Action<IAppFolderInfo, bool> onRestoreAttempted, Action onRestoreCommitted)
        {
            IAppFolderInfo restoreFolders = null;
            try
            {
                PdfSharpLicense.SetAgplLicense();

                Logger.Info("Starting Chaptarr - {0} - Version {1}",
                            Environment.ProcessPath,
                            BuildInfo.Release);

                var startupContext = new StartupContext(args);

                LongPathSupport.Enable();
                Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);

                var appMode = GetApplicationMode(startupContext);
                if (appMode == ApplicationModes.Service || appMode == ApplicationModes.Interactive)
                {
                    restoreFolders = new AppFolderInfo(startupContext);
                    var previousDatabaseExisted = File.Exists(restoreFolders.GetDatabase());
                    FullRestoreBundle.Prepare(restoreFolders);
                    if (FullRestoreBundle.IsPrepared(restoreFolders))
                    {
                        onRestoreAttempted?.Invoke(restoreFolders, previousDatabaseExisted);
                    }
                }
                var config = GetConfiguration(startupContext);

                switch (appMode)
                {
                    case ApplicationModes.Service:
                        {
                            Logger.Debug("Service selected");

                            RunHostWithRestoreCommit(CreateConsoleHostBuilder(args, startupContext).UseWindowsService(), restoreFolders, onRestoreCommitted);
                            break;
                        }

                    case ApplicationModes.Interactive:
                        {
                            Logger.Debug(trayCallback != null ? "Tray selected" : "Console selected");
                            var builder = CreateConsoleHostBuilder(args, startupContext);

                            if (trayCallback != null)
                            {
                                trayCallback(builder);
                            }

                            RunHostWithRestoreCommit(builder, restoreFolders, onRestoreCommitted);
                            break;
                        }

                    // Utility mode
                    default:
                        {
                            var utilityServices = new ServiceCollection();
                            utilityServices.AddLogging(logging =>
                            {
                                logging.ClearProviders();
                                logging.SetMinimumLevel(Microsoft.Extensions.Logging.LogLevel.Trace);
                                logging.AddNLog();
                            });
                            utilityServices.Configure<PostgresOptions>(config.GetSection("Chaptarr:Postgres"));
                            utilityServices.Configure<AppOptions>(config.GetSection("Chaptarr:App"));
                            utilityServices.Configure<AuthOptions>(config.GetSection("Chaptarr:Auth"));
                            utilityServices.Configure<ServerOptions>(config.GetSection("Chaptarr:Server"));
                            utilityServices.Configure<LogOptions>(config.GetSection("Chaptarr:Log"));
                            utilityServices.Configure<UpdateOptions>(config.GetSection("Chaptarr:Update"));

                            var utilityFactory = new DryIocServiceProviderFactory(
                                new Container(rules => rules.WithNzbDroneRules()));
                            using var utilityContainer = utilityFactory.CreateBuilder(utilityServices);
                            utilityContainer.AutoAddServices(Bootstrap.ASSEMBLIES)
                                .RegisterHttpClients()
                                .AddIndexerProxyProvider()
                                .AddNzbDroneLogger()
                                .AddDatabase()
                                .AddFuzzyMatchingServices()
                                .AddImportServices()
                                .AddNamingPatternServices()
                                // .AddHardcoverServices() // Removed - using V5 API via BookInfoProxy
                                .AddStartupContext(startupContext);

                            RegisterRealRemotePathMappingService(utilityContainer);
                            RegisterUpdatePackageProviders(utilityContainer);

                            var utilityProvider = utilityFactory.CreateServiceProvider(utilityContainer);
                            utilityProvider.GetRequiredService<IUtilityModeRouter>().Route(appMode);

                            break;
                        }
                }
            }
            catch (InvalidConfigFileException ex)
            {
                throw new ChaptarrStartupException(ex);
            }
            catch (AccessDeniedConfigFileException ex)
            {
                throw new ChaptarrStartupException(ex);
            }
            catch (TerminateApplicationException ex)
            {
                Logger.Info(ex.Message);
                LogManager.Configuration = null;
            }
            finally
            {
                if (restoreFolders != null && FullRestoreBundle.IsPrepared(restoreFolders))
                {
                    // Includes host/configuration failures before DbFactory can own rollback.
                    SqliteConnection.ClearAllPools();
                    FullRestoreBundle.Rollback(restoreFolders);
                }
            }

            // Make sure there are no lingering database connections
            GC.Collect();
            GC.WaitForPendingFinalizers();
            NpgsqlConnection.ClearAllPools();
        }

        private static void RunHostWithRestoreCommit(IHostBuilder builder, IAppFolderInfo folders, Action onRestoreCommitted)
        {
            using var host = builder.Build();
            using var registration = host.Services.GetRequiredService<IHostApplicationLifetime>().ApplicationStarted
                .Register(() =>
                {
                    FullRestoreBundle.CommitAfterStartup(folders);
                    onRestoreCommitted?.Invoke();
                });
            host.Run();
        }

        public static IHostBuilder CreateConsoleHostBuilder(string[] args, StartupContext context)
        {
            var config = GetConfiguration(context);

            var bindAddress = config.GetValue<string>($"Chaptarr:Server:{nameof(ServerOptions.BindAddress)}") ?? config.GetValue(nameof(ConfigFileProvider.BindAddress), "*");
            var port = config.GetValue<int?>($"Chaptarr:Server:{nameof(ServerOptions.Port)}") ??
                config.GetValue<int?>(nameof(ConfigFileProvider.Port)) ??
                ServerConfigurationDefaults.Port;
            var sslPort = config.GetValue<int?>($"Chaptarr:Server:{nameof(ServerOptions.SslPort)}") ?? config.GetValue(nameof(ConfigFileProvider.SslPort), 6868);
            var enableSsl = config.GetValue<bool?>($"Chaptarr:Server:{nameof(ServerOptions.EnableSsl)}") ?? config.GetValue(nameof(ConfigFileProvider.EnableSsl), false);
            var sslCertPath = config.GetValue<string>($"Chaptarr:Server:{nameof(ServerOptions.SslCertPath)}") ?? config.GetValue<string>(nameof(ConfigFileProvider.SslCertPath));
            var sslCertPassword = config.GetValue<string>($"Chaptarr:Server:{nameof(ServerOptions.SslCertPassword)}") ?? config.GetValue<string>(nameof(ConfigFileProvider.SslCertPassword));
            var metricsEnabled = config.GetValue<bool?>("Chaptarr:Metrics:Enabled") ?? config.GetValue<bool?>("MetricsEnabled") ?? false;
            var metricsPort = config.GetValue<int?>("Chaptarr:Metrics:Port") ?? config.GetValue<int?>("MetricsPort") ?? 9797;
            var metricsBindAddress = config.GetValue<string>("Chaptarr:Metrics:BindAddress") ?? config.GetValue<string>("MetricsBindAddress") ?? "127.0.0.1";

            var urls = new List<string> { BuildUrl("http", bindAddress, port) };

            if (enableSsl && sslCertPath.IsNotNullOrWhiteSpace())
            {
                urls.Add(BuildUrl("https", bindAddress, sslPort));
            }

            if (metricsEnabled)
            {
                if (metricsPort < 1 || metricsPort > 65535)
                {
                    throw new ChaptarrStartupException("Metrics port must be between 1 and 65535");
                }

                if (metricsPort == port || (enableSsl && sslCertPath.IsNotNullOrWhiteSpace() && metricsPort == sslPort))
                {
                    throw new ChaptarrStartupException("Metrics port must be different from the Chaptarr HTTP and HTTPS ports");
                }

                if (metricsBindAddress.IsNullOrWhiteSpace())
                {
                    throw new ChaptarrStartupException("Metrics bind address cannot be empty");
                }

                urls.Add(BuildUrl("http", metricsBindAddress, metricsPort));
            }

            return new HostBuilder()
                // Resolve packaged application files independently of the process working directory.
                .UseContentRoot(AppContext.BaseDirectory)
                .UseServiceProviderFactory(new DryIocServiceProviderFactory(new Container(rules => rules.WithNzbDroneRules())))
                .ConfigureContainer<IContainer>(c =>
                {
                    c.AutoAddServices(Bootstrap.ASSEMBLIES, GetDiagnosticsPluginPaths(context))
                        .RegisterHttpClients()
                        .AddIndexerProxyProvider()
                        .AddNzbDroneLogger()
                        .AddDatabase()
                        .AddFuzzyMatchingServices()
                        .AddImportServices()
                        .AddNamingPatternServices()
                        // .AddHardcoverServices() // Removed - using V5 API via BookInfoProxy
                        .AddStartupContext(context);

                    RegisterRealRemotePathMappingService(c);
                    RegisterUpdatePackageProviders(c);
                    c.Resolve<IEventAggregator>().PublishEvent(new ApplicationStartingEvent());
                })
                .ConfigureServices(services =>
                {
                    services.Configure<PostgresOptions>(config.GetSection("Chaptarr:Postgres"));
                    services.Configure<AppOptions>(config.GetSection("Chaptarr:App"));
                    services.Configure<AuthOptions>(config.GetSection("Chaptarr:Auth"));
                    services.Configure<ServerOptions>(config.GetSection("Chaptarr:Server"));
                    services.Configure<LogOptions>(config.GetSection("Chaptarr:Log"));
                    services.Configure<UpdateOptions>(config.GetSection("Chaptarr:Update"));
                })
                .ConfigureWebHost(builder =>
                {
                    builder.UseConfiguration(config);
                    builder.UseUrls(urls.ToArray());
                    builder.UseKestrel(options =>
                    {
                        if (enableSsl && sslCertPath.IsNotNullOrWhiteSpace())
                        {
                            options.ConfigureHttpsDefaults(configureOptions =>
                            {
                                configureOptions.ServerCertificate = ValidateSslCertificate(sslCertPath, sslCertPassword);
                            });
                        }
                    });
                    builder.ConfigureKestrel(serverOptions =>
                    {
                        serverOptions.AllowSynchronousIO = false;
                        serverOptions.Limits.MaxRequestBodySize = HttpSecuritySettings.GetMaxRequestBodySize(config);
                    });
                    builder.UseStartup<Startup>();
                });
        }

        private static IEnumerable<string> GetDiagnosticsPluginPaths(StartupContext context)
        {
            var appFolders = new AppFolderInfo(context);
            return DiagnosticsPluginPathResolver.Resolve(
                appFolders.AppDataFolder,
                appFolders.StartUpFolder,
                Environment.GetEnvironmentVariable("CHAPTARR_DIAGNOSTICS_ENABLED"),
                Environment.GetEnvironmentVariable("BOOKSHELF_DIAGNOSTICS_ENABLED"),
                message => Logger.Warn(message));
        }

        public static ApplicationModes GetApplicationMode(IStartupContext startupContext)
        {
            if (startupContext.Help)
            {
                return ApplicationModes.Help;
            }

            var migrateBookshelf = startupContext.MigrateBookshelf || startupContext.PreviewBookshelfMigration;
            if (startupContext.MergeBookshelfDatabases && !migrateBookshelf)
            {
                throw new InvalidOperationException("-merge-bookshelf-databases must be used with -migrate-bookshelf or -preview-bookshelf-migration.");
            }
            var checkBookshelfMigration = startupContext.CheckBookshelfMigration;
            var restoreBookshelf = startupContext.RestoreBookshelf || startupContext.PreviewBookshelfRestore;
            var postgresBackupMode = startupContext.CheckBookshelfPostgresBackup ||
                startupContext.PreviewBookshelfPostgresRestore ||
                startupContext.BackupBookshelfPostgres ||
                startupContext.RestoreBookshelfPostgres;
            var postgresUtilityCount =
                (startupContext.CheckBookshelfPostgresBackup ? 1 : 0) +
                (startupContext.PreviewBookshelfPostgresRestore ? 1 : 0) +
                (startupContext.BackupBookshelfPostgres ? 1 : 0) +
                (startupContext.RestoreBookshelfPostgres ? 1 : 0);
            if (postgresUtilityCount > 1 ||
                (postgresBackupMode && (migrateBookshelf || restoreBookshelf || checkBookshelfMigration)) ||
                (checkBookshelfMigration && (migrateBookshelf || restoreBookshelf)))
            {
                throw new InvalidOperationException("Choose one BookshelfNG migration or PostgreSQL backup utility command at a time.");
            }

            if (migrateBookshelf && restoreBookshelf)
            {
                throw new InvalidOperationException("Choose either BookshelfNG migration or BookshelfNG rollback, not both.");
            }

            if (startupContext.CheckBookshelfPostgresBackup)
            {
                return ApplicationModes.CheckBookshelfPostgresBackup;
            }

            if (startupContext.PreviewBookshelfPostgresRestore)
            {
                return ApplicationModes.PreviewBookshelfPostgresRestore;
            }

            if (startupContext.BackupBookshelfPostgres)
            {
                return ApplicationModes.BackupBookshelfPostgres;
            }

            if (startupContext.RestoreBookshelfPostgres)
            {
                return ApplicationModes.RestoreBookshelfPostgres;
            }

            if (restoreBookshelf)
            {
                return ApplicationModes.RestoreBookshelf;
            }

            if (migrateBookshelf)
            {
                return ApplicationModes.MigrateBookshelf;
            }

            if (checkBookshelfMigration)
            {
                return ApplicationModes.CheckBookshelfMigration;
            }

            if (OsInfo.IsWindows && startupContext.RegisterUrl)
            {
                return ApplicationModes.RegisterUrl;
            }

            if (OsInfo.IsWindows && startupContext.InstallService)
            {
                return ApplicationModes.InstallService;
            }

            if (OsInfo.IsWindows && startupContext.UninstallService)
            {
                return ApplicationModes.UninstallService;
            }

            Logger.Debug("Getting windows service status");

            // IsWindowsService can throw sometimes, so wrap it
            var isWindowsService = false;
            try
            {
                isWindowsService = WindowsServiceHelpers.IsWindowsService();
            }
            catch (Exception e)
            {
                Logger.Error(e, "Failed to get service status");
            }

            if (OsInfo.IsWindows && isWindowsService)
            {
                return ApplicationModes.Service;
            }

            return ApplicationModes.Interactive;
        }

        private static IConfiguration GetConfiguration(StartupContext context)
        {
            var appFolder = new AppFolderInfo(context);
            var configPath = appFolder.GetConfigPath();

            try
            {
                var configuration = new ConfigurationBuilder()
                    .AddXmlFile(configPath, optional: true, reloadOnChange: false)
                    .AddInMemoryCollection(new List<KeyValuePair<string, string>> { new("dataProtectionFolder", appFolder.GetDataProtectionPath()) })
                    .AddEnvironmentVariables()
                    .Build();

                return LegacyConfigurationCompatibility.AddFallbackSections(configuration);
            }
            catch (InvalidDataException ex)
            {
                Logger.Error(ex, ex.Message);

                throw new InvalidConfigFileException($"{configPath} is corrupt or invalid. Please delete the config file and Chaptarr will recreate it.", ex);
            }
        }

        private static string BuildUrl(string scheme, string bindAddress, int port)
        {
            if (bindAddress.Contains(":") && !bindAddress.StartsWith("[", StringComparison.Ordinal))
            {
                bindAddress = $"[{bindAddress}]";
            }

            return $"{scheme}://{bindAddress}:{port}";
        }

        private static X509Certificate2 ValidateSslCertificate(string cert, string password)
        {
            X509Certificate2 certificate;

            if (cert.IsNullOrWhiteSpace())
            {
                throw new ChaptarrStartupException("SSL certificate path is required when SSL is enabled");
            }

            if (!File.Exists(cert))
            {
                throw new ChaptarrStartupException("The SSL certificate file '{0}' does not exist", cert);
            }

            try
            {
                certificate = X509CertificateLoader.LoadPkcs12FromFile(cert, password, X509KeyStorageFlags.DefaultKeySet);
            }
            catch (CryptographicException ex)
            {
                throw new ChaptarrStartupException(ex);
            }

            return certificate;
        }
    }
}

using System;
using System.Collections.Generic;
using System.Threading;
using FluentValidation.Results;
using MQTTnet;
using NzbDrone.Common.Extensions;
using NzbDrone.Core.Configuration;
using NzbDrone.Core.ThingiProvider;
using NzbDrone.Core.Validation;

namespace NzbDrone.Core.Notifications.MqttGateway
{
    public class MqttGateway : NotificationBase<MqttGatewaySettings>, IResolveProviderPendingSecrets
    {
        private readonly IPendingProviderSecretService _pendingProviderSecretService;
        private readonly IConfigFileProvider _configFileProvider;

        public MqttGateway(IPendingProviderSecretService pendingProviderSecretService, IConfigFileProvider configFileProvider)
        {
            _pendingProviderSecretService = pendingProviderSecretService;
            _configFileProvider = configFileProvider;
        }

        public override string Name => "MQTT Gateway";
        public override string Link => "https://mqtt.org/";

        public override ValidationResult Test()
        {
            var failures = new List<ValidationFailure>();
            IMqttClient client = null;

            try
            {
                var rootTopic = MqttGatewayMqtt.GetRootTopic(Settings);
                var availabilityTopic = $"{rootTopic}/status";
                var factory = new MqttClientFactory();
                client = factory.CreateMqttClient();
                var testClientId = $"chaptarr-test-{Settings.InstanceId}-{Guid.NewGuid():N}";
                var testOptions = MqttGatewayMqtt.BuildClientOptions(Settings, availabilityTopic, testClientId, includeAvailabilityWill: false);
                using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(15));
                var connectResult = client.ConnectAsync(testOptions, timeout.Token).GetAwaiter().GetResult();

                if (!client.IsConnected)
                {
                    failures.Add(NzbDroneValidationFailure.ForMessage("Host", $"The MQTT broker rejected the connection ({connectResult.ResultCode}).", "server.message.m2024314e8436", new { value0 = connectResult.ResultCode }));
                    return new ValidationResult(failures);
                }

                var testEvent = MqttGatewayEvent.Create("test", _configFileProvider.InstallationId, _configFileProvider.InstanceName).ToJson();
                var message = MqttGatewayMqtt.BuildMessage(MqttGatewayMqtt.GetEventTopic(Settings, "test"), testEvent, Settings.EventQos);
                client.PublishAsync(message, timeout.Token).GetAwaiter().GetResult();
                client.DisconnectAsync(new MqttClientDisconnectOptionsBuilder().Build(), timeout.Token).GetAwaiter().GetResult();
            }
            catch
            {
                failures.Add(NzbDroneValidationFailure.ForMessage("Host", "Unable to connect to the MQTT broker. Check the host, port, TLS configuration, and credentials.", "server.message.ma74229566030"));
            }
            finally
            {
                client?.Dispose();
            }

            return new ValidationResult(failures);
        }

        public void ResolveProviderPendingSecrets(bool consume)
        {
            Settings.Password = _pendingProviderSecretService.Resolve(Settings.Password, consume);
        }
    }
}

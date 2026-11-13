namespace NzbDrone.Core.ThingiProvider
{
    public class ProviderMessage
    {
        public string Message { get; set; }
        public ProviderMessageType Type { get; set; }
        public string MessageId { get; set; }
        public object MessageParameters { get; set; }

        public ProviderMessage(string message, ProviderMessageType type)
        {
            Message = message;
            Type = type;
        }

        public ProviderMessage(string message, ProviderMessageType type, string messageId, object messageParameters = null)
            : this(message, type)
        {
            MessageId = messageId;
            MessageParameters = messageParameters;
        }
    }

    public enum ProviderMessageType
    {
        Info,
        Warning,
        Error
    }
}

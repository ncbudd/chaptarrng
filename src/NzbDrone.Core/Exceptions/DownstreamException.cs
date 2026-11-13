using System.Net;
using NzbDrone.Common.Exceptions;

namespace NzbDrone.Core.Exceptions
{
    public class DownstreamException : NzbDroneException
    {
        public HttpStatusCode StatusCode { get; private set; }
        public string MessageId { get; private set; }
        public object MessageParameters { get; private set; }

        public DownstreamException(HttpStatusCode statusCode, string message, params object[] args)
            : base(message, args)
        {
            StatusCode = statusCode;
        }

        public DownstreamException(HttpStatusCode statusCode, string message)
            : base(message)
        {
            StatusCode = statusCode;
        }

        protected void SetMessageId(string messageId, object messageParameters = null)
        {
            MessageId = messageId;
            MessageParameters = messageParameters;
        }
    }
}

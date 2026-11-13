using System;
using System.Net;
using NzbDrone.Common.Exceptions;

namespace NzbDrone.Core.Exceptions
{
    public class NzbDroneClientException : NzbDroneException
    {
        public HttpStatusCode StatusCode { get; private set; }
        public string MessageId { get; private set; }
        public object MessageParameters { get; private set; }

        public NzbDroneClientException(HttpStatusCode statusCode, string message, params object[] args)
            : base(message, args)
        {
            StatusCode = statusCode;
        }

        public NzbDroneClientException(HttpStatusCode statusCode, string message, Exception innerException, params object[] args)
            : base(message, innerException, args)
        {
            StatusCode = statusCode;
        }

        public NzbDroneClientException(HttpStatusCode statusCode, string message)
            : base(message)
        {
            StatusCode = statusCode;
        }

        public static NzbDroneClientException WithMessageId(HttpStatusCode statusCode, string message, string messageId)
        {
            return new NzbDroneClientException(statusCode, message)
            {
                MessageId = messageId
            };
        }

        public static NzbDroneClientException WithMessageId(HttpStatusCode statusCode, string message, string messageId, object messageParameters)
        {
            return new NzbDroneClientException(statusCode, message)
            {
                MessageId = messageId,
                MessageParameters = messageParameters
            };
        }
    }
}

using System.Net;

namespace NzbDrone.Core.Exceptions
{
    public class BadRequestException : DownstreamException
    {
        public BadRequestException(string message)
            : base(HttpStatusCode.BadRequest, message)
        {
        }

        public BadRequestException(string message, params object[] args)
            : base(HttpStatusCode.BadRequest, message, args)
        {
        }

        public static BadRequestException WithMessageId(string message, string messageId, object messageParameters = null)
        {
            var exception = new BadRequestException(message);
            exception.SetMessageId(messageId, messageParameters);
            return exception;
        }
    }
}

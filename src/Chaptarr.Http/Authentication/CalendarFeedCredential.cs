using System;
using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Http;

namespace Chaptarr.Http.Authentication
{
    // A subscription can outlive browser sessions, but must never grant API access.
    // Rotating the master key also revokes every existing calendar subscription.
    public static class CalendarFeedCredential
    {
        public static string Issue(string apiKey)
        {
            if (string.IsNullOrEmpty(apiKey))
            {
                throw new InvalidOperationException("A configured API key is required.");
            }

            var digest = HMACSHA256.HashData(Encoding.UTF8.GetBytes(apiKey),
                Encoding.UTF8.GetBytes("Chaptarr/calendar-feed/v1"));
            return "cal_" + Convert.ToHexString(digest);
        }

        public static bool Validate(HttpRequest request, string token, string apiKey)
        {
            if (string.IsNullOrEmpty(apiKey) || token == null || token.Length != 68 ||
                !HttpMethods.IsGet(request.Method) ||
                !(request.Path.Equals(new PathString("/feed/v1/calendar/Chaptarr.ics"), StringComparison.OrdinalIgnoreCase) ||
                  request.Path.Equals(new PathString("/feed/v1/calendar/Readarr.ics"), StringComparison.OrdinalIgnoreCase)))
            {
                return false;
            }

            return CryptographicOperations.FixedTimeEquals(
                Encoding.UTF8.GetBytes(Issue(apiKey)), Encoding.UTF8.GetBytes(token));
        }
    }
}

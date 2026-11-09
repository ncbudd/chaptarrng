using Chaptarr.Http;
using Chaptarr.Http.Authentication;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using NzbDrone.Core.Configuration;

namespace Chaptarr.Api.V1.Calendar
{
    [V1ApiController("calendar/token")]
    [Authorize(Policy = "AdminApiKey")]
    public class CalendarTokenController : Controller
    {
        private readonly IConfigFileProvider _config;

        public CalendarTokenController(IConfigFileProvider config)
        {
            _config = config;
        }

        [HttpGet]
        [ResponseCache(NoStore = true, Location = ResponseCacheLocation.None)]
        public object GetToken() => new { Token = CalendarFeedCredential.Issue(_config.ApiKey) };
    }
}

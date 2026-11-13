using System.Threading.Tasks;
using Chaptarr.Http.Authentication;
using Microsoft.AspNetCore.Http;
using NUnit.Framework;

namespace Chaptarr.Core.Test.Authentication
{
    [TestFixture]
    public class SeerrApiKeyAccessPolicyFixture
    {
        [Test]
        public async Task should_allow_bounded_local_book_search_for_seerr_service_key()
        {
            var context = CreateLibrarySearchContext("?term=Winteraustern&limit=50&mediaType=ebook");

            Assert.That(await SeerrApiKeyAccessPolicy.IsAllowedAsync(context.Request), Is.True);
        }

        [TestCase("?term=Winteraustern&limit=0&mediaType=ebook")]
        [TestCase("?term=Winteraustern&limit=51&mediaType=ebook")]
        [TestCase("?term=Winteraustern&mediaType=both")]
        [TestCase("?term=Winteraustern&unexpected=1")]
        [TestCase("?term=Winteraustern&term=Another%20Book")]
        [TestCase("?limit=50&mediaType=ebook")]
        [TestCase("?term=%20%20&limit=50")]
        public async Task should_reject_invalid_local_book_search_parameters(string query)
        {
            var context = CreateLibrarySearchContext(query);

            Assert.That(await SeerrApiKeyAccessPolicy.IsAllowedAsync(context.Request), Is.False);
        }

        [Test]
        public async Task should_reject_local_book_search_terms_over_256_characters()
        {
            var context = CreateLibrarySearchContext("?term=" + new string('a', 257));

            Assert.That(await SeerrApiKeyAccessPolicy.IsAllowedAsync(context.Request), Is.False);
        }

        private static DefaultHttpContext CreateLibrarySearchContext(string query)
        {
            var context = new DefaultHttpContext();
            context.Request.Method = HttpMethods.Get;
            context.Request.Path = "/api/v1/library/search";
            context.Request.QueryString = new QueryString(query);
            return context;
        }
    }
}

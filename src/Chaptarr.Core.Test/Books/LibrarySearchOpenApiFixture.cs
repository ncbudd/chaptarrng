using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using NUnit.Framework;

namespace Chaptarr.Core.Test.Books
{
    [TestFixture]
    public class LibrarySearchOpenApiFixture
    {
        [Test]
        public void openapi_documents_the_optional_library_search_media_type_values()
        {
            using var stream = Assembly.GetExecutingAssembly()
                .GetManifestResourceStream("Chaptarr.Core.Test.Contracts.openapi.json");
            Assert.That(stream, Is.Not.Null, "The checked-in OpenAPI schema must be embedded for contract assertions.");

            using var document = JsonDocument.Parse(stream);
            var operation = document.RootElement
                .GetProperty("paths")
                .GetProperty("/api/v1/library/search")
                .GetProperty("get");
            var mediaType = operation.GetProperty("parameters")
                .EnumerateArray()
                .Single(parameter => parameter.GetProperty("name").GetString() == "mediaType");

            Assert.That(mediaType.GetProperty("in").GetString(), Is.EqualTo("query"));
            Assert.That(mediaType.TryGetProperty("required", out var required) && required.GetBoolean(), Is.False);
            Assert.That(mediaType.GetProperty("description").GetString(), Does.Contain("single media type"));
            Assert.That(mediaType.GetProperty("schema").GetProperty("enum").EnumerateArray()
                .Select(value => value.GetString()), Is.EqualTo(new[] { "ebook", "audiobook" }));
        }
    }
}

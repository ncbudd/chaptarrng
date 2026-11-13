using Chaptarr.Http;
using Chaptarr.Api.V1.MediaTypes;
using System.Collections.Generic;
using Microsoft.AspNetCore.Mvc;
using NzbDrone.Core.Books;
using NzbDrone.Core.Books.Services;
using NzbDrone.Core.MediaCover;

namespace Chaptarr.Api.V1.Search
{
    [V1ApiController("library/search")]
    public class LibrarySearchController : Controller
    {
        private readonly ILibrarySearchService _librarySearchService;
        private readonly IMapCoversToLocal _coverMapper;

        public LibrarySearchController(ILibrarySearchService librarySearchService, IMapCoversToLocal coverMapper)
        {
            _librarySearchService = librarySearchService;
            _coverMapper = coverMapper;
        }

        [HttpGet]
        public LibrarySearchResult Search([FromQuery] string term, [FromQuery] int limit = 10, [FromQuery] string mediaType = null)
        {
            var parsedMediaType = MediaTypeParameterParser.ParseOptional(mediaType, allowAll: false);
            var results = _librarySearchService.Search(term, limit, parsedMediaType);

            foreach (var author in results.Authors)
            {
                author.Images ??= new List<MediaCover>();
                _coverMapper.ConvertToLocalUrls(author.Id, MediaCoverEntity.Author, author.Images, author.SelectedPosterHash);
            }

            foreach (var book in results.Books)
            {
                book.Images ??= new List<MediaCover>();
                _coverMapper.ConvertToLocalUrls(book.Id, MediaCoverEntity.Book, book.Images);
            }

            return results;
        }
    }
}

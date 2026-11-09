using Chaptarr.Http;
using Chaptarr.Http.REST;
using NUnit.Framework;
using NzbDrone.Core.Datastore;

namespace Chaptarr.Core.Test.Http
{
    [TestFixture]
    public class PagingResourceMapperFixture
    {
        private class TestModel
        {
        }

        private static PagingResource<TestModel> BuildResource(int page, int pageSize)
        {
            return new PagingResource<TestModel>(new PagingRequestResource
            {
                Page = page,
                PageSize = pageSize
            });
        }

        [TestCase(1)]
        [TestCase(10)]
        [TestCase(1000)]
        [TestCase(2000)]
        public void should_pass_page_size_through_unchanged(int pageSize)
        {
            var spec = BuildResource(1, pageSize).MapToPagingSpec<TestModel, TestModel>();

            Assert.That(spec.PageSize, Is.EqualTo(pageSize));
        }

        [TestCase(0)]
        [TestCase(-1)]
        public void should_reject_page_size_below_one(int pageSize)
        {
            Assert.Throws<BadRequestException>(() => BuildResource(1, pageSize).MapToPagingSpec<TestModel, TestModel>());
        }

        [TestCase(0)]
        [TestCase(-1)]
        public void should_reject_page_below_one(int page)
        {
            Assert.Throws<BadRequestException>(() => BuildResource(page, 10).MapToPagingSpec<TestModel, TestModel>());
        }

        [TestCase(1, 2001)]
        [TestCase(1, int.MaxValue)]
        [TestCase(int.MaxValue, 2000)]
        [TestCase(1000001, 1000)]
        public void should_reject_unbounded_or_overflowing_pages(int page, int pageSize)
        {
            Assert.Throws<BadRequestException>(() => BuildResource(page, pageSize).MapToPagingSpec<TestModel, TestModel>());
        }
    }
}

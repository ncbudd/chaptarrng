using SkiaSharp;

namespace NzbDrone.Core.MediaCover
{
    public static class RasterImagePolicy
    {
        public static bool TryGetContentType(byte[] bytes, out string contentType)
        {
            contentType = null;
            if (bytes == null || bytes.Length == 0 || bytes.Length > 20 * 1024 * 1024)
            {
                return false;
            }

            using var data = SKData.CreateCopy(bytes);
            using var codec = SKCodec.Create(data);
            if (codec == null || codec.Info.Width <= 0 || codec.Info.Height <= 0 ||
                (long)codec.Info.Width * codec.Info.Height > 40_000_000)
            {
                return false;
            }

            contentType = codec.EncodedFormat switch
            {
                SKEncodedImageFormat.Jpeg => "image/jpeg",
                SKEncodedImageFormat.Png => "image/png",
                SKEncodedImageFormat.Gif => "image/gif",
                SKEncodedImageFormat.Webp => "image/webp",
                SKEncodedImageFormat.Bmp => "image/bmp",
                SKEncodedImageFormat.Avif => "image/avif",
                _ => null
            };
            return contentType != null;
        }
    }
}

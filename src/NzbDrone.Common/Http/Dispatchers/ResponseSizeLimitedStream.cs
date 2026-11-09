using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace NzbDrone.Common.Http.Dispatchers
{
    internal sealed class ResponseSizeLimitedStream : Stream
    {
        private readonly Stream _destination;
        private readonly long _limit;
        private long _written;
        public ResponseSizeLimitedStream(Stream destination, long limit) { _destination = destination; _limit = limit; }
        public override bool CanRead => false;
        public override bool CanSeek => false;
        public override bool CanWrite => true;
        public override long Length => _written;
        public override long Position { get => _written; set => throw new NotSupportedException(); }
        public override void Flush() => _destination.Flush();
        public override Task FlushAsync(CancellationToken cancellationToken) => _destination.FlushAsync(cancellationToken);
        public override int Read(byte[] buffer, int offset, int count) => throw new NotSupportedException();
        public override long Seek(long offset, SeekOrigin origin) => throw new NotSupportedException();
        public override void SetLength(long value) => throw new NotSupportedException();
        private void Reserve(int count)
        {
            if (count > _limit - _written) { throw new InvalidDataException("HTTP response exceeds the configured byte limit."); }
            _written += count;
        }

        public override void Write(byte[] buffer, int offset, int count)
        {
            Reserve(count);
            _destination.Write(buffer, offset, count);
        }

        public override Task WriteAsync(byte[] buffer, int offset, int count, CancellationToken cancellationToken)
        {
            Reserve(count);
            return _destination.WriteAsync(buffer, offset, count, cancellationToken);
        }

        public override ValueTask WriteAsync(ReadOnlyMemory<byte> buffer, CancellationToken cancellationToken = default)
        {
            Reserve(buffer.Length);
            return _destination.WriteAsync(buffer, cancellationToken);
        }
    }
}

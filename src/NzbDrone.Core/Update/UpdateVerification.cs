using System;
using NzbDrone.Common.Disk;
using NzbDrone.Common.Extensions;

namespace NzbDrone.Core.Update
{
    public interface IVerifyUpdates
    {
        bool Verify(UpdatePackage updatePackage, string packagePath);
    }

    public class UpdateVerification : IVerifyUpdates
    {
        private readonly IDiskProvider _diskProvider;
        private readonly IUpdateAttestationVerifier _attestations;

        public UpdateVerification(IDiskProvider diskProvider, IUpdateAttestationVerifier attestations)
        {
            _diskProvider = diskProvider;
            _attestations = attestations;
        }

        public bool Verify(UpdatePackage updatePackage, string packagePath)
        {
            if (updatePackage == null || updatePackage.Hash.IsNullOrWhiteSpace())
            {
                return false;
            }

            using (var fileStream = _diskProvider.OpenReadStream(packagePath))
            {
                var hash = fileStream.SHA256Hash();

                return hash.Equals(updatePackage.Hash, StringComparison.OrdinalIgnoreCase) && _attestations.Verify(updatePackage, packagePath);
            }
        }
    }
}

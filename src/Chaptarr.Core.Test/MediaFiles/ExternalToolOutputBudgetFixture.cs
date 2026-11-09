using System;
using System.Reflection;
using System.Threading;
using Moq;
using NLog;
using NUnit.Framework;
using NzbDrone.Common.Disk;
using NzbDrone.Common.EnvironmentInfo;
using NzbDrone.Core.Configuration;
using NzbDrone.Core.MediaFiles;

namespace Chaptarr.Core.Test.MediaFiles
{
    [TestFixture]
    [Platform("Linux")]
    public class ExternalToolOutputBudgetFixture
    {
        [TestCase(false)]
        [TestCase(true)]
        public void noisy_child_process_is_stopped_without_retaining_unbounded_output(bool stderr)
        {
            var folders = new Mock<IAppFolderInfo>();
            folders.SetupGet(f => f.AppDataFolder).Returns(TestContext.CurrentContext.WorkDirectory);
            folders.SetupGet(f => f.StartUpFolder).Returns(TestContext.CurrentContext.TestDirectory);
            var service = new ExternalToolsService(new Mock<IConfigService>().Object, new Mock<IDiskProvider>().Object,
                folders.Object, LogManager.GetCurrentClassLogger());
            var execute = typeof(ExternalToolsService).GetMethod("ExecuteCommandDetailed", BindingFlags.NonPublic | BindingFlags.Instance);
            var result = (ExternalToolResult)execute.Invoke(service, new object[]
            {
                "/bin/sh", new[] { "-c", "head -c 6291456 /dev/zero" + (stderr ? " >&2" : string.Empty) },
                10000, null, CancellationToken.None, null
            });
            Assert.That(result.Succeeded, Is.False);
            Assert.That(result.TimedOut, Is.False);
            Assert.That(result.ErrorMessage, Does.Contain("output budget"));
            Assert.That(result.StandardOutput.Length + result.StandardError.Length, Is.LessThanOrEqualTo(ExternalToolsService.MaximumCapturedOutputChars));
        }
    }
}

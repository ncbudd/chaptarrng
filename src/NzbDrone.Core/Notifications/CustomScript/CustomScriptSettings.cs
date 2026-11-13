using System.Linq;
using FluentValidation;
using NzbDrone.Common.Disk;
using NzbDrone.Common.Extensions;
using NzbDrone.Core.Annotations;
using NzbDrone.Core.ThingiProvider;
using NzbDrone.Core.Validation;
using NzbDrone.Core.Validation.Paths;

namespace NzbDrone.Core.Notifications.CustomScript
{
    public class CustomScriptSettingsValidator : AbstractValidator<CustomScriptSettings>
    {
        public CustomScriptSettingsValidator()
        {
            RuleFor(c => c.Path).IsValidPath();
            RuleFor(c => c.Path)
                .SetValidator(new SystemFolderValidator())
                .WithMessage("Must not be a descendant of '{systemFolder}'")
                .WithState(settings => NzbDroneValidationState.ForMessage(
                    "server.message.mc78af077e86e",
                    new
                    {
                        value0 = SystemFolders.GetSystemFolders().FirstOrDefault(folder =>
                            folder.PathEquals(settings.Path) || folder.IsParentPath(settings.Path))
                    }));
            RuleFor(c => c.Arguments).Empty().WithMessage("Arguments are no longer supported for custom scripts")
                .WithState(_ => NzbDroneValidationState.ForMessage("server.message.m2ebae1c36a6c"));
        }
    }

    public class CustomScriptSettings : IProviderConfig
    {
        private static readonly CustomScriptSettingsValidator Validator = new CustomScriptSettingsValidator();

        [FieldDefinition(0, Label = "Path", Type = FieldType.FilePath)]
        public string Path { get; set; }

        [FieldDefinition(1, Label = "provider.field.f7f816072c1c6", HelpText = "provider.field.fd35c546d4b1a", Hidden = HiddenType.HiddenIfNotSet)]
        public string Arguments { get; set; }

        public NzbDroneValidationResult Validate()
        {
            return new NzbDroneValidationResult(Validator.Validate(this));
        }
    }
}

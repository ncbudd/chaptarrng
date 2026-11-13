import PropTypes from 'prop-types';
import React from 'react';
import FormInputHelpText from 'Components/Form/FormInputHelpText';
import SpinnerErrorButton from 'Components/Link/SpinnerErrorButton';
import { kinds } from 'Helpers/Props';
import translate from 'Utilities/String/translate';

function getOAuthErrorMessages(error) {
  if (!error) {
    return [];
  }

  const responseJSON = error.responseJSON;

  if (Array.isArray(responseJSON)) {
    const messages = responseJSON
      .map((failure, index) => typeof failure === 'string' ?
        { message: failure } :
        {
          message: failure?.errorMessage || failure?.message,
          messageKey: index === 0 ? error.appMessageKey : undefined,
          messageId: failure?.messageId || failure?.errorMessageId,
          messageParameters: failure?.messageParameters
        })
      .filter(({ message }) => typeof message === 'string' && message.trim());

    if (messages.length) {
      return messages;
    }

    return typeof error.responseText === 'string' && error.responseText.trim() ?
      [{ message: error.responseText }] :
      [];
  }

  if (typeof responseJSON === 'string' && responseJSON.trim()) {
    return [{ message: responseJSON }];
  }

  if (responseJSON && typeof responseJSON === 'object') {
    const message = responseJSON.message || responseJSON.errorMessage || error.responseText;
    return typeof message === 'string' && message.trim() ? [{
      message,
      messageKey: error.appMessageKey,
      messageId: responseJSON.messageId || responseJSON.errorMessageId,
      messageParameters: responseJSON.messageParameters
    }] : [];
  }

  return typeof error.responseText === 'string' && error.responseText.trim() ?
    [{ message: error.responseText }] :
    [];
}

function OAuthInput(props) {
  const {
    label,
    authorizing,
    error,
    providerData,
    onPress
  } = props;

  const errorMessages = getOAuthErrorMessages(error);
  const buttonLabel = label || translate('StartOAuth');

  const implementationName = providerData && typeof providerData.implementationName === 'string' ?
    providerData.implementationName :
    '';

  const isPlex = implementationName.toLowerCase().includes('plex');
  const kind = isPlex ? kinds.WARNING : kinds.PRIMARY;

  return (
    <div>
      <SpinnerErrorButton
        kind={kind}
        isSpinning={authorizing}
        error={error}
        onPress={onPress}
      >
        {buttonLabel}
      </SpinnerErrorButton>

      {
        errorMessages.map((errorMessage, index) => (
          <FormInputHelpText
            key={`oauth-error-${index}`}
            text={errorMessage.message}
            messageKey={errorMessage.messageKey}
            messageId={errorMessage.messageId}
            messageParameters={errorMessage.messageParameters}
            messageMode={errorMessage.messageKey || errorMessage.messageId ? 'source' : 'opaque'}
            isError={true}
          />
        ))
      }
    </div>
  );
}

OAuthInput.propTypes = {
  label: PropTypes.string,
  authorizing: PropTypes.bool.isRequired,
  error: PropTypes.object,
  providerData: PropTypes.object,
  onPress: PropTypes.func.isRequired
};

OAuthInput.defaultProps = {};

export default OAuthInput;

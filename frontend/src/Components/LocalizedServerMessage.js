import PropTypes from 'prop-types';
import React from 'react';
import BidiText from 'Components/BidiText';
import { translateServerMessageById } from 'Utilities/String/translateServerMessage';

function LocalizedServerMessage({ message, messageId, messageParameters }) {
  const translated = translateServerMessageById(messageId, messageParameters);

  if (translated) {
    return translated;
  }

  return typeof message === 'string' && message ?
    <BidiText lang="und">{message}</BidiText> :
    null;
}

LocalizedServerMessage.propTypes = {
  message: PropTypes.string,
  messageId: PropTypes.string,
  messageParameters: PropTypes.object
};

export default LocalizedServerMessage;

import classNames from 'classnames';
import PropTypes from 'prop-types';
import React from 'react';
import BidiText from 'Components/BidiText';
import Icon from 'Components/Icon';
import Link from 'Components/Link/Link';
import { icons } from 'Helpers/Props';
import isolateBidiText from 'Utilities/String/isolateBidiText';
import translate from 'Utilities/String/translate';
import translateServerMessage, { translateServerMessageById } from 'Utilities/String/translateServerMessage';
import styles from './FormInputHelpText.css';

function FormInputHelpText(props) {
  const {
    className,
    id,
    text,
    messageKey,
    messageId,
    messageParameters,
    messageMode,
    link,
    tooltip,
    isError,
    isWarning,
    isCheckInput
  } = props;
  const translatedById = messageId ? translateServerMessageById(messageId, messageParameters) : null;
  const translatedText = messageKey ?
    translate(messageKey, messageParameters) :
    translatedById ||
    (messageMode === 'opaque' || messageId ? <BidiText lang="und">{text}</BidiText> : translateServerMessage(text));
  const translatedTooltip = messageMode === 'opaque' && tooltip ? isolateBidiText(tooltip) : translateServerMessage(tooltip);

  return (
    <div
      id={id}
      className={classNames(
        className,
        isError && styles.isError,
        isWarning && styles.isWarning,
        isCheckInput && styles.isCheckInput
      )}
    >
      {translatedText}

      {
        link ?
          <Link
            className={styles.link}
            to={link}
            title={translatedTooltip}
          >
            <Icon
              name={icons.EXTERNAL_LINK}
            />
          </Link> :
          null
      }

      {
        !link && tooltip ?
          <Icon
            containerClassName={styles.details}
            name={icons.INFO}
            title={translatedTooltip}
          /> :
          null
      }
    </div>
  );
}

FormInputHelpText.propTypes = {
  className: PropTypes.string.isRequired,
  id: PropTypes.string,
  text: PropTypes.string.isRequired,
  messageKey: PropTypes.string,
  messageId: PropTypes.string,
  messageParameters: PropTypes.object,
  messageMode: PropTypes.oneOf(['source', 'opaque']),
  link: PropTypes.string,
  tooltip: PropTypes.string,
  isError: PropTypes.bool,
  isWarning: PropTypes.bool,
  isCheckInput: PropTypes.bool
};

FormInputHelpText.defaultProps = {
  className: styles.helpText,
  isError: false,
  isWarning: false,
  isCheckInput: false
};

export default FormInputHelpText;

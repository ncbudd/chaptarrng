import PropTypes from 'prop-types';
import React from 'react';
import Alert from 'Components/Alert';
import LocalizedServerMessage from 'Components/LocalizedServerMessage';
import { kinds } from 'Helpers/Props';
import translateServerMessage from 'Utilities/String/translateServerMessage';
import styles from './Form.css';

function Form(props) {
  const {
    children,
    validationErrors,
    validationWarnings,
    successMessages,
    serverMessageMode,
    // eslint-disable-next-line no-unused-vars
    ...otherProps
  } = props;

  return (
    <div>
      {
        successMessages.length || validationErrors.length || validationWarnings.length ?
          <div className={styles.validationFailures}>
            {
              successMessages.map((msg, index) => {
                return (
                  <Alert
                    key={`success-${index}`}
                    kind={kinds.SUCCESS}
                  >
                    {renderServerMessage(msg, serverMessageMode)}
                  </Alert>
                );
              })
            }

            {
              validationErrors.map((error, index) => {
                return (
                  <Alert
                    key={`error-${index}`}
                    kind={kinds.DANGER}
                  >
                    {renderServerMessage(error, serverMessageMode)}
                  </Alert>
                );
              })
            }

            {
              validationWarnings.map((warning, index) => {
                return (
                  <Alert
                    key={`warning-${index}`}
                    kind={kinds.WARNING}
                  >
                    {renderServerMessage(warning, serverMessageMode)}
                  </Alert>
                );
              })
            }
          </div> :
          null
      }

      {children}
    </div>
  );
}

function renderServerMessage(message, mode) {
  if (message && typeof message === 'object') {
    const text = message.message ?? message.errorMessage;
    const localized = <LocalizedServerMessage
      message={text}
      messageId={message.messageId ?? message.errorMessageId}
      messageParameters={message.messageParameters}
    />;

    if (mode === 'opaque' || message.messageId || message.errorMessageId) {
      return localized;
    }

    return translateServerMessage(text);
  }

  if (mode === 'opaque') {
    return <LocalizedServerMessage message={message} />;
  }

  return translateServerMessage(message);
}

Form.propTypes = {
  children: PropTypes.node.isRequired,
  validationErrors: PropTypes.arrayOf(PropTypes.object).isRequired,
  validationWarnings: PropTypes.arrayOf(PropTypes.object).isRequired,
  successMessages: PropTypes.arrayOf(PropTypes.oneOfType([PropTypes.string, PropTypes.object])),
  serverMessageMode: PropTypes.oneOf(['source', 'opaque'])
};

Form.defaultProps = {
  validationErrors: [],
  validationWarnings: [],
  successMessages: [],
  serverMessageMode: 'source'
};

export default Form;

import PropTypes from 'prop-types';
import React, { Component } from 'react';
import Alert from 'Components/Alert';
import Form from 'Components/Form/Form';
import FormGroup from 'Components/Form/FormGroup';
import FormInputButton from 'Components/Form/FormInputButton';
import FormInputGroup from 'Components/Form/FormInputGroup';
import FormLabel from 'Components/Form/FormLabel';
import Icon from 'Components/Icon';
import Button from 'Components/Link/Button';
import ClipboardButton from 'Components/Link/ClipboardButton';
import LoadingIndicator from 'Components/Loading/LoadingIndicator';
import ModalBody from 'Components/Modal/ModalBody';
import ModalContent from 'Components/Modal/ModalContent';
import ModalFooter from 'Components/Modal/ModalFooter';
import ModalHeader from 'Components/Modal/ModalHeader';
import { icons, inputTypes, kinds, sizes } from 'Helpers/Props';
import createAjaxRequest from 'Utilities/createAjaxRequest';
import translate from 'Utilities/String/translate';

function getUrls(state) {
  const {
    unmonitored,
    pastDays,
    futureDays,
    tags,
    calendarToken
  } = state;

  if (!calendarToken) {
    return { iCalHttpUrl: '', iCalWebCalUrl: '' };
  }

  let icalUrl = `${window.location.host}${window.Chaptarr.urlBase}/feed/v1/calendar/Chaptarr.ics?`;

  if (unmonitored) {
    icalUrl += 'unmonitored=true&';
  }

  if (tags.length) {
    icalUrl += `tags=${tags.toString()}&`;
  }

  icalUrl += `pastDays=${pastDays}&futureDays=${futureDays}&calendarToken=${encodeURIComponent(calendarToken)}`;

  const iCalHttpUrl = `${window.location.protocol}//${icalUrl}`;
  const iCalWebCalUrl = `webcal://${icalUrl}`;

  return {
    iCalHttpUrl,
    iCalWebCalUrl
  };
}

class CalendarLinkModalContent extends Component {

  //
  // Lifecycle

  constructor(props, context) {
    super(props, context);

    const defaultState = {
      unmonitored: false,
      pastDays: 7,
      futureDays: 28,
      tags: [],
      calendarToken: null,
      isLoading: true,
      hasError: false
    };

    const urls = getUrls(defaultState);

    this.state = {
      ...defaultState,
      ...urls
    };
  }

  componentDidMount() {
    this.onLoadTokenPress();
  }

  componentWillUnmount() {
    this.unmounted = true;
    this.tokenRequest?.abortRequest();
  }

  onLoadTokenPress = () => {
    this.setState({ isLoading: true, hasError: false });
    this.tokenRequest = createAjaxRequest({ url: '/calendar/token', dataType: 'json' });
    this.tokenRequest.request.done(({ token }) => {
      if (!this.unmounted) {
        this.setState((state) => ({
          calendarToken: token,
          isLoading: false,
          ...getUrls({ ...state, calendarToken: token })
        }));
      }
    }).fail(() => {
      if (!this.unmounted) {
        this.setState({ isLoading: false, hasError: true });
      }
    });
  };

  //
  // Listeners

  onInputChange = ({ name, value }) => {
    const state = {
      ...this.state,
      [name]: value
    };

    const urls = getUrls(state);

    this.setState({
      [name]: value,
      ...urls
    });
  };

  onLinkFocus = (event) => {
    event.target.select();
  };

  //
  // Render

  render() {
    const {
      onModalClose
    } = this.props;

    const {
      unmonitored,
      pastDays,
      futureDays,
      tags,
      isLoading,
      hasError,
      iCalHttpUrl,
      iCalWebCalUrl
    } = this.state;

    return (
      <ModalContent onModalClose={onModalClose}>
        <ModalHeader>
          {translate('ChaptarrCalendarFeed')}
        </ModalHeader>

        <ModalBody>
          {isLoading ? <LoadingIndicator /> : null}
          {hasError ? (
            <Alert kind={kinds.DANGER} role="alert">
              {translate('UnableToLoadTheCalendar')}
              <Button onPress={this.onLoadTokenPress}>{translate('Retry')}</Button>
            </Alert>
          ) : null}
          {!isLoading && !hasError ? <Form>
            <FormGroup>
              <FormLabel>
                {translate('IncludeUnmonitored')}
              </FormLabel>

              <FormInputGroup
                type={inputTypes.CHECK}
                name="unmonitored"
                value={unmonitored}
                helpText={translate('UnmonitoredHelpText')}
                onChange={this.onInputChange}
              />
            </FormGroup>

            <FormGroup>
              <FormLabel>
                {translate('PastDays')}
              </FormLabel>

              <FormInputGroup
                type={inputTypes.NUMBER}
                name="pastDays"
                value={pastDays}
                helpText={translate('PastDaysHelpText')}
                onChange={this.onInputChange}
              />
            </FormGroup>

            <FormGroup>
              <FormLabel>
                {translate('FutureDays')}
              </FormLabel>

              <FormInputGroup
                type={inputTypes.NUMBER}
                name="futureDays"
                value={futureDays}
                helpText={translate('FutureDaysHelpText')}
                onChange={this.onInputChange}
              />
            </FormGroup>

            <FormGroup>
              <FormLabel>
                {translate('Tags')}
              </FormLabel>

              <FormInputGroup
                type={inputTypes.TAG}
                name="tags"
                value={tags}
                helpText={translate('TagsHelpText')}
                onChange={this.onInputChange}
              />
            </FormGroup>

            <FormGroup
              size={sizes.LARGE}
            >
              <FormLabel>
                {translate('ICalFeed')}
              </FormLabel>

              <FormInputGroup
                type={inputTypes.TEXT}
                name="iCalHttpUrl"
                value={iCalHttpUrl}
                readOnly={true}
                helpText={translate('ICalHttpUrlHelpText')}
                buttons={[
                  <ClipboardButton
                    key="copy"
                    value={iCalHttpUrl}
                    kind={kinds.DEFAULT}
                  />,

                  <FormInputButton
                    key="webcal"
                    kind={kinds.DEFAULT}
                    to={iCalWebCalUrl}
                    target="_blank"
                    noRouter={true}
                  >
                    <Icon name={icons.CALENDAR_O} />
                  </FormInputButton>
                ]}
                onChange={this.onInputChange}
                onFocus={this.onLinkFocus}
              />
            </FormGroup>
          </Form> : null}
        </ModalBody>

        <ModalFooter>
          <Button onPress={onModalClose}>
            {translate('Close')}
          </Button>
        </ModalFooter>
      </ModalContent>
    );
  }
}

CalendarLinkModalContent.propTypes = {
  tagList: PropTypes.arrayOf(PropTypes.object).isRequired,
  onModalClose: PropTypes.func.isRequired
};

export default CalendarLinkModalContent;

const assert = require('node:assert/strict');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { transformSync } = require('@babel/core');

const propType = () => propType;
propType.isRequired = propType;
const PropTypes = new Proxy({}, { get: () => propType });
function Component(props) { this.props = props; this.state = {}; }
Component.prototype.setState = function(update) {
  this.state = { ...this.state, ...(typeof update === 'function' ? update(this.state) : update) };
};
const React = {
  Component,
  createElement: (type, props, ...children) => ({ type, props: { ...props, children } })
};
function load(relativePath, mocks, window) {
  const filename = path.join(__dirname, relativePath);
  const { code } = transformSync(fs.readFileSync(filename, 'utf8'), {
    filename, babelrc: false, configFile: false,
    presets: [['@babel/preset-env', { targets: { node: 'current' }, modules: 'commonjs' }], '@babel/preset-react']
  });
  const modules = {
    react: { __esModule: true, default: React, Component },
    'prop-types': { __esModule: true, default: PropTypes },
    'Helpers/Props': { icons: {}, inputTypes: {}, kinds: {}, sizes: {} },
    'Utilities/String/translate': { __esModule: true, default: (key) => key },
    ...mocks
  };
  const sandbox = {
    exports: {}, window, console: { log() {} }, setInterval: () => 1, clearInterval() {},
    require: (name) => modules[name] || { __esModule: true, default: name }
  };
  vm.runInNewContext(code, sandbox, { filename });
  return sandbox.exports.default;
}
function find(element, type) {
  if (Array.isArray(element)) return element.flatMap((child) => find(child, type));
  if (!element || typeof element !== 'object') return [];
  return [...(element.type === type ? [element] : []), ...find(element.props?.children, type)];
}
function calendarModal() {
  const requests = [];
  const Calendar = load('Calendar/iCal/CalendarLinkModalContent.js', {
    'Utilities/createAjaxRequest': { __esModule: true, default: (options) => {
      const entry = { ...options, aborted: false };
      const request = {
        done(callback) { entry.resolve = callback; return request; },
        fail(callback) { entry.reject = callback; return request; }
      };
      requests.push(entry);
      return { request, abortRequest() { entry.aborted = true; entry.reject(); } };
    } }
  }, { location: { host: 'books.example', protocol: 'https:' }, Chaptarr: { urlBase: '/books', apiKey: 'ui_private' } });
  const modal = new Calendar({ tagList: [], onModalClose() {} });
  modal.componentDidMount();
  return { modal, requests };
}

test('calendar subscription uses its dedicated credential, preserves filters and never copies the browser token', () => {
  const { modal, requests } = calendarModal();
  assert.equal(requests[0].url, '/calendar/token');
  assert.equal(modal.state.iCalHttpUrl, '');
  assert.equal(find(modal.render(), 'Components/Form/Form').length, 0);
  requests[0].resolve({ token: 'cal_subscription' });
  modal.onInputChange({ name: 'tags', value: [4, 7] });
  modal.onInputChange({ name: 'unmonitored', value: true });
  const url = new URL(modal.state.iCalHttpUrl);
  assert.equal(url.pathname, '/books/feed/v1/calendar/Chaptarr.ics');
  assert.equal(url.searchParams.get('calendarToken'), 'cal_subscription');
  assert.equal(url.searchParams.get('tags'), '4,7');
  assert.equal(url.searchParams.get('unmonitored'), 'true');
  assert.equal(url.searchParams.has('apikey'), false);
  assert.equal(modal.state.iCalHttpUrl.includes('ui_private'), false);
  assert.ok(modal.state.iCalWebCalUrl.startsWith('webcal://'));
  const field = find(modal.render(), 'Components/Form/FormInputGroup').find((item) => item.props.name === 'iCalHttpUrl');
  assert.equal(field.props.buttons[0].props.value, modal.state.iCalHttpUrl);
});

test('failed subscription credential fetch exposes retry and no unusable feed link', () => {
  const { modal, requests } = calendarModal();
  requests[0].reject();
  const alert = find(modal.render(), 'Components/Alert')[0];
  assert.equal(alert.props.role, 'alert');
  assert.equal(find(modal.render(), 'Components/Form/Form').length, 0);
  find(alert, 'Components/Link/Button')[0].props.onPress();
  requests[1].resolve({ token: 'cal_retry' });
  assert.equal(modal.state.hasError, false);
  assert.ok(modal.state.iCalHttpUrl.includes('cal_retry'));
});

test('closing calendar modal aborts its request without updating the unmounted component', () => {
  const { modal, requests } = calendarModal();
  const before = modal.state;
  modal.componentWillUnmount();
  requests[0].resolve({ token: 'cal_late' });
  assert.equal(requests[0].aborted, true);
  assert.equal(modal.state, before);
});

test('SignalR reconnect refreshes credentials and redacts stale tokens from diagnostics', async () => {
  const captured = {};
  class HubConnectionBuilder {
    configureLogging(logger) { captured.logger = logger; return this; }
    withUrl(url, options) { captured.url = url; captured.options = options; return this; }
    withAutomaticReconnect() { return this; }
    build() {
      return { onreconnecting() {}, onreconnected() {}, onclose() {}, on() {}, start: () => ({ then() {} }) };
    }
  }
  const window = { Chaptarr: { urlBase: '/books', apiKey: 'ui_before' } };
  let refreshes = 0;
  const Connector = load('Components/SignalRConnector.js', {
    '@microsoft/signalr/dist/browser/signalr.js': { HubConnectionBuilder, LogLevel: { Information: 2 } },
    'react-redux': { connect: () => (component) => component },
    'Utilities/refreshUiSession': { __esModule: true, default: async () => {
      refreshes++;
      if (refreshes === 1) throw new Error('server still restarting');
      window.Chaptarr.apiKey = 'ui_renewed';
    } }
  }, window);
  const connector = new Connector({ dispatchSetAppValue() {} });
  connector.restoreImportState = () => {};
  connector.componentDidMount();
  assert.equal(captured.url, '/books/signalr/messages');
  assert.equal(await captured.options.accessTokenFactory(), 'ui_before');
  window.Chaptarr.apiKey = 'ui_after';
  assert.equal(await captured.options.accessTokenFactory(), 'ui_after');
  connector.onReconnecting();
  await assert.rejects(captured.options.accessTokenFactory(), /server still restarting/);
  assert.equal(await captured.options.accessTokenFactory(), 'ui_renewed');
  assert.equal(await captured.options.accessTokenFactory(), 'ui_renewed');
  assert.equal(refreshes, 2);
  assert.equal(captured.logger.cleanse('retry /signalr?access_token=ui_before&other=1'), 'retry /signalr?access_token=(removed)&other=1');
});

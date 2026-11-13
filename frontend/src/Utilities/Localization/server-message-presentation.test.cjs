const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');
const { transformSync } = require('@babel/core');
const React = require('react');
const PropTypes = require('prop-types');
const { renderToStaticMarkup } = require('react-dom/server');
const matching = require('./server-message-match.cjs');
const records = require('./server-messages.json');

function loadComponent(file, dependencies) {
  const { code } = transformSync(fs.readFileSync(file, 'utf8'), {
    filename: file,
    babelrc: false,
    configFile: false,
    plugins: ['@babel/plugin-transform-react-jsx', '@babel/plugin-transform-modules-commonjs']
  });
  const sandbox = {
    exports: {},
    require(name) {
      if (Object.hasOwn(dependencies, name)) {
        return dependencies[name];
      }
      throw new Error(`Unexpected component dependency: ${name}`);
    }
  };
  vm.runInNewContext(code, sandbox, { filename: file });
  return sandbox.exports.default;
}

function loadBidiText() {
  const helperFile = path.resolve(__dirname, '../String/isolateBidiText.js');
  const { code } = transformSync(fs.readFileSync(helperFile, 'utf8'), {
    filename: helperFile,
    babelrc: false,
    configFile: false,
    plugins: ['@babel/plugin-transform-modules-commonjs']
  });
  const helperSandbox = { exports: {} };
  vm.runInNewContext(code, helperSandbox, { filename: helperFile });

  return loadComponent(path.resolve(__dirname, '../../Components/BidiText.js'), {
    react: React,
    'prop-types': PropTypes,
    'Utilities/String/isolateBidiText': {
      sanitizeBidiText: helperSandbox.exports.sanitizeBidiText
    }
  });
}

function loadInteractiveSearchRow() {
  const helperFile = path.resolve(__dirname, '../String/isolateBidiText.js');
  const { code: helperCode } = transformSync(fs.readFileSync(helperFile, 'utf8'), {
    filename: helperFile,
    babelrc: false,
    configFile: false,
    plugins: ['@babel/plugin-transform-modules-commonjs']
  });
  const helperSandbox = { exports: {} };
  vm.runInNewContext(helperCode, helperSandbox, { filename: helperFile });
  const sanitizeBidiText = helperSandbox.exports.sanitizeBidiText;
  const styles = new Proxy({}, { get: (_target, key) => key });
  const values = new Proxy({}, { get: (_target, key) => key });
  const component = { __esModule: true, default: 'MockComponent' };
  const callable = { __esModule: true, default: () => '' };
  const dependencies = {
    classnames: { __esModule: true, default: (...names) => names.filter(Boolean).join(' ') },
    'prop-types': PropTypes,
    react: React,
    'Activity/Queue/ProtocolLabel': component,
    'Book/BookFormats': component,
    'Book/BookQuality': component,
    'Book/IndexerFlags': component,
    'Components/BidiText': loadBidiText(),
    'Components/Icon': component,
    'Components/Label': component,
    'Components/Link/Link': component,
    'Components/Link/SpinnerIconButton': { __esModule: true, default: 'SpinnerIconButton' },
    'Components/Modal/ConfirmModal': component,
    'Components/Table/Cells/TableRowCell': component,
    'Components/Table/TableRow': component,
    'Components/Table/TableRow.css': { __esModule: true, default: styles },
    'Components/Tooltip/Popover': component,
    'Components/Tooltip/Tooltip': component,
    'Helpers/Props': { icons: values, kinds: values, tooltipPositions: values },
    'Utilities/Date/formatDateTime': callable,
    'Utilities/Number/formatAge': callable,
    'Utilities/Number/formatBytes': callable,
    'Utilities/Number/formatCustomFormatScore': callable,
    'Utilities/String/isolateBidiText': { sanitizeBidiText },
    'Utilities/String/translate': { __esModule: true, default: (key) => key },
    'Utilities/String/translateServerMessage': {
      translateServerMessageById(messageId) {
        return messageId === 'validated' ? '\u2068Localized error\u2069' : null;
      }
    },
    './Peers': component,
    './InteractiveSearchRow.css': { __esModule: true, default: styles }
  };

  return loadComponent(path.resolve(__dirname, '../../InteractiveSearch/InteractiveSearchRow.js'), dependencies);
}

function findElement(element, type) {
  if (Array.isArray(element)) {
    return element.map((child) => findElement(child, type)).find(Boolean) || null;
  }

  if (!React.isValidElement(element)) {
    return null;
  }

  if (element.type === type) {
    return element;
  }

  return findElement(element.props.children, type);
}

function loadPresenter(translations, matchServerMessage = matching.matchServerMessage) {
  const file = path.resolve(__dirname, '../String/translateServerMessage.js');
  const bidiHelperFile = path.resolve(__dirname, '../String/isolateBidiText.js');
  const { code: bidiHelperCode } = transformSync(fs.readFileSync(bidiHelperFile, 'utf8'), {
    filename: bidiHelperFile, babelrc: false, configFile: false,
    plugins: ['@babel/plugin-transform-modules-commonjs']
  });
  const bidiHelperSandbox = { exports: {} };
  vm.runInNewContext(bidiHelperCode, bidiHelperSandbox, { filename: bidiHelperFile });
  const isolateBidiText = bidiHelperSandbox.exports.default;
  const { code } = transformSync(fs.readFileSync(file, 'utf8'), {
    filename: file, babelrc: false, configFile: false,
    plugins: ['@babel/plugin-transform-modules-commonjs']
  });
  const sandbox = {
    exports: {},
    require(name) {
      if (name.endsWith('server-message-match.cjs')) {
        return { ...matching, matchServerMessage };
      }
      if (name.endsWith('server-messages.json')) {
        return records;
      }
      if (name === 'Utilities/String/isolateBidiText') {
        return isolateBidiText;
      }
      if (name === 'Utilities/String/translate') {
        return {
          translateWithFallback(id, source, tokens) {
            return (translations[id] || source).replace(/\{([^{}]+)\}/g,
              (literal, key) => (Object.hasOwn(tokens, key) ? tokens[key] : literal));
          }
        };
      }
      throw new Error(`Unexpected presenter dependency: ${name}`);
    }
  };
  vm.runInNewContext(code, sandbox, { filename: file });
  const present = sandbox.exports.default;
  present.byId = sandbox.exports.translateServerMessageById;
  present.isolateBidiText = isolateBidiText;
  return present;
}

test('real expanded state/path errors traverse the presentation helper and preserve data', () => {
  const present = loadPresenter({
    'server.message.m0a3d9d1876f5': 'حالة تنزيل غير معروفة: {value0}',
    'server.message.mc78af077e86e': 'يجب ألا يكون داخل المسار {value0}'
  });
  assert.equal(present('Unknown download state: pausedUP'), 'حالة تنزيل غير معروفة: \u2068pausedUP\u2069');
  const folder = '/opt/Book 01 - كتاب/{id}';
  assert.equal(present(`Must not be a descendant of '${folder}'`), `يجب ألا يكون داخل المسار \u2068${folder}\u2069`);
  assert.equal(present('A provider wrote arbitrary exception text'), '\u2068A provider wrote arbitrary exception text\u2069');
});

test('literal Hardcover ID examples are never interpreted as dynamic placeholders', () => {
  const present = loadPresenter({
    'server.message.m50abcbe9b4b1': 'المعرّف المدعوم هو hc:{id}'
  });
  assert.equal(present('Only Hardcover series IDs are currently supported (expected hc:{id})'), 'المعرّف المدعوم هو hc:{id}');
});

test('presentation isolation preserves the complete mixed-script capture and the original stored message', () => {
  const present = loadPresenter({ 'server.message.m064135c5401a': 'المسار {value0} غير موجود' });
  const pathValue = '/mnt/Book 01 - كتاب [QA]/file.epub';
  const stored = { message: `Path '${pathValue}' does not exist` };
  const original = stored.message;
  assert.equal(present(stored.message), `المسار \u2068${pathValue}\u2069 غير موجود`);
  assert.equal(stored.message, original);
  assert.deepEqual(matching.matchServerMessage(stored.message, matching.compileServerMessageMatchers(records)).tokens, {
    value0: pathValue
  });
});

test('shared presentation helpers do not add nested isolation to an English fallback message', () => {
  const present = loadPresenter({});
  const raw = 'Path \'/books/Book 01 - كتاب\' does not exist';
  const once = present(raw);
  assert.equal(once, 'Path \'\u2068/books/Book 01 - كتاب\u2069\' does not exist');
  assert.equal(present(once), once);
});

test('oversized server messages isolate without entering matchers or marker scans', () => {
  let matchCalls = 0;
  const present = loadPresenter({}, (...args) => {
    matchCalls++;
    return matching.matchServerMessage(...args);
  });
  const raw = `prefix${' Converted file retained at: '.repeat(400)}${'x'.repeat(8192)}`;

  assert.equal(present(raw), `\u2068${raw}\u2069`);
  assert.equal(matchCalls, 0);
});

test('unmatched server messages scrub bidi controls and remain idempotent', () => {
  const present = loadPresenter({});
  const raw = 'Provider message: Book\u2069\u202Eapproved\u202C';
  const safe = '\u2068Provider message: Bookapproved\u2069';

  assert.equal(present(raw), safe);
  assert.equal(present(present(raw)), safe);
});

test('oversized messages scrub bidi controls without running matchers', () => {
  let matchCalls = 0;
  const present = loadPresenter({}, (...args) => {
    matchCalls++;
    return matching.matchServerMessage(...args);
  });
  const raw = `prefix\u2069\u202E${' Converted file retained at: '.repeat(400)}${'x'.repeat(8192)}`;
  const safe = `\u2068${raw.replace(/[\u061C\u200E\u200F\u202A-\u202E\u2066-\u206F]/g, '')}\u2069`;

  assert.equal(present(raw), safe);
  assert.equal(present(safe), safe);
  assert.equal(matchCalls, 0);
});

test('failed alternate-client localization scrubs unsafe fallback controls', () => {
  const present = loadPresenter({});
  const raw = 'No enabled torrent download client is configured. Found 2 enabled strange\u2069\u202E client(s). Add and enable a torrent-capable download client, then retry.';
  const safe = '\u2068No enabled torrent download client is configured. Found 2 enabled strange client(s). Add and enable a torrent-capable download client, then retry.\u2069';

  assert.equal(present(raw), safe);
  assert.equal(present(present(raw)), safe);
});

test('new notification/grab/detail presentation resolves synthetic Arabic without changing stored data', () => {
  const source = 'This torrent is already present in {value0} as \'{value1}\'.';
  const record = records.find((entry) => entry.source === source);
  const present = loadPresenter({ [record.id]: 'موجود في {value0}: {value1}' });
  const client = 'client/{value1}/العربية';
  const title = '/books/Book (2026)';
  const stored = { message: `This torrent is already present in ${client} as '${title}'.` };
  const original = JSON.stringify(stored);
  assert.equal(present(stored.message), `موجود في \u2068${client}\u2069: \u2068${title}\u2069`);
  assert.equal(JSON.stringify(stored), original);
  assert.equal(present('Downloading'), '\u2068Downloading\u2069');
});

test('display-only message values cannot close or bypass their directional isolate', () => {
  const present = loadPresenter({
    'server.message.m064135c5401a': 'المسار {value0} غير موجود'
  });
  const embeddedControls = 'Book\u2069\u202Eapproved\u202C\u206B';
  const preIsolatedControls = '\u2068Book\u2069\u202Eapproved\u202C\u2069';
  const expected = 'المسار \u2068Bookapproved\u2069 غير موجود';
  const stored = { message: `Path '${embeddedControls}' does not exist` };
  const original = stored.message;

  assert.equal(present(stored.message), expected);
  assert.equal(present.byId('server.message.m064135c5401a', { value0: preIsolatedControls }), expected);
  assert.equal(present.isolateBidiText(embeddedControls), '\u2068Bookapproved\u2069');
  assert.equal(stored.message, original);
});

test('opaque and localized fallback components sanitize direct and nested rendered strings', () => {
  const BidiText = loadBidiText();
  const LocalizedServerMessage = loadComponent(path.resolve(__dirname, '../../Components/LocalizedServerMessage.js'), {
    react: React,
    'prop-types': PropTypes,
    'Components/BidiText': BidiText,
    'Utilities/String/translateServerMessage': {
      translateServerMessageById: () => null
    }
  });
  const Message = loadComponent(path.resolve(__dirname, '../../Components/Page/Sidebar/Messages/Message.js'), {
    react: React,
    'prop-types': PropTypes,
    classnames: (...values) => values.filter(Boolean).join(' '),
    'Components/BidiText': BidiText,
    'Components/Icon': () => React.createElement('span'),
    'Helpers/Props': { icons: new Proxy({}, { get: (_target, name) => name }) },
    'Utilities/String/translate': () => 'translated',
    'Utilities/String/translateServerMessage': {
      __esModule: true,
      default: (message) => message,
      translateServerMessageById: () => null
    },
    './ImportProgressMessage': () => React.createElement('span'),
    './Message.css': {
      __esModule: true,
      default: { message: 'message', error: 'error' }
    }
  });
  const attack = 'External Book\u2069\u202Espoof\u202C';
  const safe = 'External Bookspoof';
  const balancedRaw = 'External \u2067Book\u2069 and \u2068Title\u2069';
  const balancedSafe = 'External Book and Title';
  const directOpaque = React.createElement(BidiText, { lang: 'und' }, attack,
    React.createElement('span', { key: 'nested' }, ' nested\u2069\u202Evalue\u202C'));
  const localizedFallback = React.createElement(LocalizedServerMessage, { message: attack, messageId: 'missing.id' });
  const balancedLocalizedFallback = React.createElement(LocalizedServerMessage, { message: balancedRaw, messageId: 'missing.id' });
  const opaqueMessage = React.createElement(Message, {
    name: 'SeriesAddError', message: attack, messageMode: 'opaque', type: 'error'
  });
  const localizedMessage = React.createElement(Message, {
    name: 'SeriesAddError', message: attack, messageMode: 'localized', type: 'error'
  });

  for (const element of [directOpaque, localizedFallback, opaqueMessage, localizedMessage]) {
    const html = renderToStaticMarkup(element);

    assert.doesNotMatch(html, /[\u061C\u200E\u200F\u202A-\u202E\u2066-\u206F]/);
    assert.match(html, /External Bookspoof|External Book/);
  }

  assert.equal(renderToStaticMarkup(localizedFallback), `<bdi dir="auto" lang="und">${safe}</bdi>`);
  assert.equal(renderToStaticMarkup(balancedLocalizedFallback), `<bdi dir="auto" lang="und">${balancedSafe}</bdi>`);

  const knownLocalizedMessage = React.createElement(BidiText, {
    lang: 'ar',
    preserveBalancedIsolates: true
  }, 'رسالة \u2068Book\u2069');
  assert.equal(
    renderToStaticMarkup(knownLocalizedMessage),
    '<bdi dir="auto" lang="ar">رسالة \u2068Book\u2069</bdi>'
  );
});

test('interactive-search download title strips raw controls and keeps validated localized isolates', () => {
  const InteractiveSearchRow = loadInteractiveSearchRow();
  const baseProps = {
    rank: 1,
    guid: 'release-guid',
    protocol: 'torrent',
    age: 0,
    ageHours: 0,
    ageMinutes: 0,
    publishDate: '2026-01-01T00:00:00Z',
    title: 'Book',
    infoUrl: 'https://example.test/release',
    indexer: 'indexer',
    indexerId: 1,
    size: 1,
    quality: {},
    customFormats: [],
    customFormatScore: 0,
    indexerFlags: 0,
    rejections: [],
    downloadAllowed: true,
    isGrabbing: false,
    isGrabbed: false,
    longDateFormat: 'YYYY-MM-DD',
    timeFormat: 'HH:mm',
    searchPayload: {},
    onGrabPress: () => undefined
  };
  const attack = 'Provider error\u2069\u202Espoof\u202C';
  const rawRow = new InteractiveSearchRow({ ...baseProps, grabError: attack });
  const rawButton = findElement(rawRow.render(), 'SpinnerIconButton');
  const rawTitleMarkup = renderToStaticMarkup(React.createElement('button', { title: rawButton.props.title }, 'Grab'));

  assert.equal(rawButton.props.title, 'Provider errorspoof');
  assert.equal(rawTitleMarkup, '<button title="Provider errorspoof">Grab</button>');

  const localizedRow = new InteractiveSearchRow({
    ...baseProps,
    grabError: attack,
    grabErrorMessageId: 'validated'
  });
  const localizedButton = findElement(localizedRow.render(), 'SpinnerIconButton');

  assert.equal(localizedButton.props.title, '\u2068Localized error\u2069');
});

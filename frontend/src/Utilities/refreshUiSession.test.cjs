const assert = require('node:assert/strict');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { transformSync } = require('@babel/core');

function load(file, sandbox) {
  const filename = path.join(__dirname, file);
  const { code } = transformSync(fs.readFileSync(filename, 'utf8'), {
    filename, babelrc: false, configFile: false,
    presets: [['@babel/preset-env', { targets: { node: 'current' }, modules: 'commonjs' }], '@babel/preset-typescript']
  });
  const context = { exports: {}, ...sandbox };
  vm.runInNewContext(code, context, { filename });
  return context.exports.default;
}
const token = 'ui_' + 'A'.repeat(64);

test('concurrent refreshes share a request and update the credential only after authenticated initialization', async () => {
  let finish;
  let calls = 0;
  const window = { Chaptarr: { urlBase: '/books', apiKey: 'ui_old' } };
  const refresh = load('refreshUiSession.ts', { window, fetch(url, options) {
    calls++;
    assert.equal(url, '/books/initialize.json');
    assert.equal(options.credentials, 'same-origin');
    assert.equal(options.cache, 'no-store');
    return new Promise((resolve) => { finish = resolve; });
  } });
  const first = refresh();
  const second = refresh();
  assert.equal(first, second);
  assert.equal(window.Chaptarr.apiKey, 'ui_old');
  finish({ ok: true, json: async () => ({ apiKey: token }) });
  assert.equal(await first, token);
  assert.equal(await second, token);
  assert.equal(window.Chaptarr.apiKey, token);
  assert.equal(calls, 1);
  const third = refresh();
  finish({ ok: true, json: async () => ({ apiKey: token }) });
  await third;
  assert.equal(calls, 2);
});

test('failed and malformed refreshes never downgrade to a master key and permit a later retry', async () => {
  const responses = [
    { ok: false },
    { ok: true, json: async () => ({ apiKey: 'master-key' }) },
    { ok: true, json: async () => ({ apiKey: token }) }
  ];
  const window = { Chaptarr: { urlBase: '', apiKey: 'ui_old' } };
  const refresh = load('refreshUiSession.ts', { window, fetch: async () => responses.shift() });
  await assert.rejects(refresh(), /refresh failed/);
  await assert.rejects(refresh(), /Invalid browser/);
  assert.equal(window.Chaptarr.apiKey, 'ui_old');
  assert.equal(await refresh(), token);
});

// Minimal jqXHR/Deferred adapter preserves the callback tuple used by this
// wrapper. Network requests remain under test control, including abort timing.
function jq(promise) {
  return {
    then(done, fail) {
      const invoke = (callback, args, rejected) => {
        if (!callback) return rejected ? Promise.reject(args) : args;
        const value = callback(...args);
        if (value && typeof value.then === 'function') {
          return new Promise((resolve, reject) => value.then((...a) => resolve(a), (...a) => reject(a)));
        }
        return [value];
      };
      return jq(promise.then((a) => invoke(done, a, false), (a) => invoke(fail, a, true)));
    },
    done(callback) { promise.then((a) => { callback(...a); }, () => {}); return this; },
    fail(callback) { promise.then(() => {}, (a) => { callback(...a); }); return this; },
    always(callback) { return jq(promise.then((a) => { callback(); return a; }, (a) => { callback(); throw a; })); },
    promise() { return this; }
  };
}
function deferred() {
  let resolve, reject;
  const result = jq(new Promise((yes, no) => { resolve = yes; reject = no; }));
  result.resolve = (...args) => { resolve(args); return result; };
  result.reject = (...args) => { reject(args); return result; };
  return result;
}
function ajaxHarness(refreshImplementation) {
  const requests = [];
  let refreshes = 0;
  const window = { Chaptarr: { apiRoot: '/api/v1', apiKey: 'ui_old' }, XMLHttpRequest: function() { this.abort = () => {}; } };
  const create = load('createAjaxRequest.js', {
    window,
    require(name) {
      if (name === 'jquery') return { __esModule: true, default: { Deferred: deferred, ajax(options) {
        const result = deferred();
        const xhr = options.xhr();
        xhr.abort = () => result.reject({ status: 0 }, 'abort', 'abort');
        requests.push({ ...options, headers: { ...options.headers }, result, xhr });
        return result;
      } } };
      if (name === './refreshUiSession') return { __esModule: true, default: async () => {
        refreshes++;
        await refreshImplementation?.();
        window.Chaptarr.apiKey = token;
      } };
      throw new Error('Unexpected module: ' + name);
    }
  });
  return { create, requests, refreshes: () => refreshes };
}
const flush = () => new Promise((resolve) => setImmediate(resolve));
const outcome = (request) => new Promise((resolve) => request.done((value) => resolve({ value })).fail((xhr) => resolve({ xhr })));

test('expired UI request refreshes and retries once with a fresh XHR and the same operation', async () => {
  const h = ajaxHarness();
  const { request } = h.create({ url: '/config/host', method: 'PUT', data: '{"name":"value"}', dataType: 'json' });
  const result = outcome(request);
  h.requests[0].result.reject({ status: 401 }, 'error', 'Unauthorized');
  await flush();
  assert.equal(h.refreshes(), 1);
  assert.equal(h.requests.length, 2);
  assert.equal(h.requests[1].headers['X-Api-Key'], token);
  assert.equal(h.requests[1].method, 'PUT');
  assert.equal(h.requests[1].data, h.requests[0].data);
  assert.notEqual(h.requests[1].xhr, h.requests[0].xhr);
  h.requests[1].result.resolve({ saved: true });
  assert.deepEqual((await result).value, { saved: true });
});

test('a second unauthorized response is returned without an authentication retry loop', async () => {
  const h = ajaxHarness();
  const result = outcome(h.create({ url: '/book' }).request);
  h.requests[0].result.reject({ status: 401 });
  await flush();
  h.requests[1].result.reject({ status: 401 });
  assert.equal((await result).xhr.status, 401);
  assert.equal(h.requests.length, 2);
  assert.equal(h.refreshes(), 1);
});

test('abort during shared credential refresh never replays the cancelled operation', async () => {
  let finish;
  const h = ajaxHarness(() => new Promise((resolve) => { finish = resolve; }));
  const operation = h.create({ url: '/book', method: 'POST' });
  const result = outcome(operation.request);
  h.requests[0].result.reject({ status: 401 });
  await flush();
  operation.abortRequest();
  finish();
  assert.equal((await result).xhr.aborted, true);
  assert.equal(h.requests.length, 1);
});

test('failed refresh and external requests return the original error without replay', async () => {
  const h = ajaxHarness(() => Promise.reject(new Error('login required')));
  const result = outcome(h.create({ url: '/book' }).request);
  h.requests[0].result.reject({ status: 401 });
  assert.equal((await result).xhr.status, 401);
  assert.equal(h.requests.length, 1);
  const external = outcome(h.create({ url: 'https://provider.example/resource' }).request);
  h.requests[1].result.reject({ status: 401 });
  assert.equal((await external).xhr.status, 401);
  assert.equal(h.refreshes(), 1);
});

import $ from 'jquery';
import refreshUiSession from './refreshUiSession';

const absUrlRegex = /^(https?:)?\/\//i;

function isRelative(ajaxOptions) {
  return !absUrlRegex.test(ajaxOptions.url);
}

function addRootUrl(ajaxOptions) {
  const apiRoot = window.Chaptarr.apiRoot;
  ajaxOptions.url = apiRoot + ajaxOptions.url;
}

function addApiKey(ajaxOptions) {
  ajaxOptions.headers = ajaxOptions.headers || {};
  ajaxOptions.headers['X-Api-Key'] = window.Chaptarr.apiKey;
  ajaxOptions.headers['X-ChaptarrNG-Client'] = 'native';
}

function addContentType(ajaxOptions) {
  if (
    ajaxOptions.contentType == null &&
    ajaxOptions.dataType === 'json' &&
    (ajaxOptions.method === 'PUT' || ajaxOptions.method === 'POST' || ajaxOptions.method === 'DELETE')) {
    ajaxOptions.contentType = 'application/json';
  }
}

export default function createAjaxRequest(originalAjaxOptions) {
  let requestXHR = new window.XMLHttpRequest();
  let aborted = false;
  let complete = false;

  function abortRequest() {
    if (!complete) {
      aborted = true;
      requestXHR.abort();
    }
  }

  const ajaxOptions = { ...originalAjaxOptions };
  const usesUiSession = isRelative(ajaxOptions) && window.Chaptarr.apiKey?.startsWith('ui_');

  if (isRelative(ajaxOptions)) {
    addRootUrl(ajaxOptions);
    addApiKey(ajaxOptions);
    addContentType(ajaxOptions);
  }

  const send = () => $.ajax({
    xhr: () => requestXHR,
    ...ajaxOptions
  });

  const request = send().then(null, (xhr, textStatus, errorThrown) => {
    if (!aborted && usesUiSession && xhr.status === 401) {
      const retry = $.Deferred();
      refreshUiSession().then(() => {
        if (aborted) {
          retry.reject(xhr, textStatus, errorThrown);
          return;
        }

        requestXHR = new window.XMLHttpRequest();
        addApiKey(ajaxOptions);
        // A 401 is rejected by authentication before the API action executes.
        // Retry once only; a second rejection is delivered to the caller.
        send().done((...args) => retry.resolve(...args)).fail((...args) => retry.reject(...args));
      }, () => {
        retry.reject(xhr, textStatus, errorThrown);
      });
      return retry.promise();
    }

    return $.Deferred().reject(xhr, textStatus, errorThrown).promise();
  }).then(null, (xhr, textStatus, errorThrown) => {
    xhr.aborted = aborted;

    return $.Deferred().reject(xhr, textStatus, errorThrown).promise();
  }).always(() => {
    complete = true;
  });

  return {
    request,
    abortRequest
  };
}

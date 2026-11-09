let pendingRefresh: Promise<string> | undefined = undefined;

// Share one refresh across simultaneous API failures. Authentication still comes
// from the browser's existing HttpOnly cookie (or HTTP authentication session).
export default function refreshUiSession(): Promise<string> {
  if (!pendingRefresh) {
    pendingRefresh = (async () => {
      const response = await fetch(
        `${window.Chaptarr.urlBase}/initialize.json`,
        {
          cache: 'no-store',
          credentials: 'same-origin',
        }
      );
      if (!response.ok) {
        throw new Error('Browser session refresh failed');
      }

      const { apiKey } = await response.json();
      if (typeof apiKey !== 'string' || !/^ui_[A-Fa-f0-9]{64}$/.test(apiKey)) {
        throw new Error('Invalid browser session credential');
      }

      window.Chaptarr.apiKey = apiKey;
      return apiKey;
    })().finally(() => {
      pendingRefresh = undefined;
    });
  }

  return pendingRefresh;
}

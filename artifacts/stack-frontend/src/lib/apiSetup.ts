import { setAuthTokenGetter, setBaseUrl } from "@workspace/api-client-react";

export function setupApi() {
  // OpenAPI already prefixes paths with /api, so avoid double-prefixing.
  setBaseUrl(null);
  setAuthTokenGetter(() => {
    const saved = localStorage.getItem("stack_auth");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.access_token;
      } catch (e) {
        return null;
      }
    }
    return null;
  });
}

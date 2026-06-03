const DATA_SOURCE_ENDPOINT = "/api/v1/admin/settings/data-source";

function getAuthHeaders() {
  const headers = {
    "Content-Type": "application/json",
  };

  const saved = localStorage.getItem("stack_auth");
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      if (parsed?.access_token) {
        headers.Authorization = `Bearer ${parsed.access_token}`;
      }
    } catch (error) {
      // Ignore malformed auth cache.
    }
  }

  return headers;
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    credentials: "include",
    ...options,
    headers: {
      ...getAuthHeaders(),
      ...(options.headers || {}),
    },
  });

  const responseText = await response.text();
  let data = null;

  if (responseText) {
    try {
      data = JSON.parse(responseText);
    } catch (error) {
      data = { detail: responseText };
    }
  }

  if (!response.ok) {
    const error = new Error(data?.detail || "Request failed");
    error.data = data;
    throw error;
  }

  return data;
}

export async function getDataSource() {
  return requestJson(DATA_SOURCE_ENDPOINT);
}

export async function setDataSource(mode) {
  return requestJson(DATA_SOURCE_ENDPOINT, {
    method: "PATCH",
    body: JSON.stringify({ mode }),
  });
}
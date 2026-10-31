const BASE = import.meta.env.VITE_API_URL || "";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = `The archive returned ${res.status}.`;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") detail = data.detail;
      else if (Array.isArray(data.detail)) detail = data.detail[0]?.msg || detail;
    } catch {
      /* keep the generic message */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  health: () => request("/api/health"),
  scan: (source) =>
    request("/api/scan", { method: "POST", body: JSON.stringify({ source }) }),
  demo: () => request("/api/demo", { method: "POST" }),
  haunt: (scanId) => request(`/api/scan/${scanId}/haunt`, { method: "POST" }),
  seance: (scanId, question, history) =>
    request(`/api/scan/${scanId}/seance`, {
      method: "POST",
      body: JSON.stringify({ question, history }),
    }),
  discard: (scanId) =>
    fetch(`${BASE}/api/scan/${scanId}`, { method: "DELETE" }).catch(() => {}),
  exportUrl: (scanId) => `${BASE}/api/scan/${scanId}/export`,
};

export { BASE };

const API_BASE = "";

function getToken() {
  return localStorage.getItem("token") || "";
}

function getRole() {
  return localStorage.getItem("role") || "";
}

async function apiRequest(path, options = {}) {
  const headers = options.headers || {};
  headers["Content-Type"] = headers["Content-Type"] || "application/json";

  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (response.status === 401) {
    localStorage.clear();
    window.location.href = "index.html";
    return;
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "Request failed");
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response;
}

async function downloadFile(path, filename) {
  const token = getToken();
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error("Failed to download file");
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
}

function showToast(message, type = "info") {
  let wrap = document.getElementById("toastWrap");
  if (!wrap) {
    wrap = document.createElement("div");
    wrap.id = "toastWrap";
    wrap.className = "toast-wrap";
    document.body.appendChild(wrap);
  }
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  wrap.appendChild(el);
  setTimeout(() => el.remove(), 2800);
}

function getStatusBadgeClass(status) {
  const value = (status || "").toLowerCase();
  if (["active", "available", "assigned", "returned"].includes(value)) return "badge success";
  if (["under repair", "inactive", "retired"].includes(value)) return "badge warning";
  if (["lost"].includes(value)) return "badge danger";
  return "badge";
}

function renderEmptyRow(tbodyId, colSpan, message) {
  const body = document.getElementById(tbodyId);
  if (!body) return;
  body.innerHTML = `<tr><td colspan="${colSpan}" class="empty">${message}</td></tr>`;
}

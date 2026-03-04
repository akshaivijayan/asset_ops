if (document.getElementById("reportBody")) {
  requireAuth();
  if (!isAdmin()) {
    document.getElementById("importBox").classList.add("hidden");
  }
  loadPreview();
}

const previewLoaderMap = {
  "assets-by-employee": "/api/reports/assets-by-employee",
  "unassigned-assets": "/api/reports/unassigned-assets",
  "under-repair": "/api/reports/under-repair",
  "warranty-expiring": "/api/reports/warranty-expiring",
};

document.getElementById("reportName")?.addEventListener("change", loadPreview);

async function loadPreview() {
  try {
    const reportName = document.getElementById("reportName").value;
    const rows = await apiRequest(previewLoaderMap[reportName]);

    const head = document.getElementById("reportHead");
    const body = document.getElementById("reportBody");

    if (!rows.length) {
      head.innerHTML = "";
      renderEmptyRow("reportBody", 1, "No data available for this report.");
      return;
    }

    const keys = Object.keys(rows[0]);
    head.innerHTML = `<tr>${keys.map((k) => `<th>${k}</th>`).join("")}</tr>`;
    body.innerHTML = rows
      .slice(0, 100)
      .map((row) => `<tr>${keys.map((k) => `<td>${row[k] ?? ""}</td>`).join("")}</tr>`)
      .join("");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function downloadReport() {
  try {
    const reportName = document.getElementById("reportName").value;
    const format = document.getElementById("format").value;
    const ext = format === "excel" ? "xlsx" : "csv";
    await downloadFile(`/api/reports/export/${reportName}?fmt=${format}`, `${reportName}.${ext}`);
    showToast("Report downloaded", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function importEmployees() {
  if (!isAdmin()) return;
  const input = document.getElementById("empFile");
  if (!input.files.length) {
    showToast("Select employees file", "info");
    return;
  }

  try {
    const formData = new FormData();
    formData.append("file", input.files[0]);
    await uploadForm("/api/reports/import/employees", formData);
    showToast("Employees imported", "success");
    loadPreview();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function importAssets() {
  if (!isAdmin()) return;
  const input = document.getElementById("assetFile");
  if (!input.files.length) {
    showToast("Select assets file", "info");
    return;
  }

  try {
    const formData = new FormData();
    formData.append("file", input.files[0]);
    await uploadForm("/api/reports/import/assets", formData);
    showToast("Assets imported", "success");
    loadPreview();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function uploadForm(path, formData) {
  if (IS_GH_PAGES) {
    return apiRequest(path, { method: "POST", body: JSON.stringify({}) });
  }

  const token = getToken();
  const response = await fetch(path, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "Upload failed");
  }

  return response.json();
}

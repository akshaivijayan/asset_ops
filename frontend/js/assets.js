let editingAssetId = null;

if (document.getElementById("assetRows")) {
  requireAuth();
  if (!isAdmin()) {
    document.getElementById("addAssetBtn").classList.add("hidden");
  }
  loadAssets();

  document.getElementById("addAssetBtn")?.addEventListener("click", () => openAssetModal());
  document.getElementById("assetForm").addEventListener("submit", saveAsset);
  document.getElementById("exportAssetsBtn")?.addEventListener("click", exportAssets);
}

async function loadAssets() {
  try {
    const params = new URLSearchParams();
    ["search", "category", "status", "assigned_employee"].forEach((id) => {
      const value = document.getElementById(id).value.trim();
      if (value) params.append(id, value);
    });

    const rows = await apiRequest(`/api/assets?${params.toString()}`);
    const body = document.getElementById("assetRows");

    if (!rows.length) {
      renderEmptyRow("assetRows", 7, "No assets matched your filters.");
      return;
    }

    body.innerHTML = rows
      .map(
        (row) => `
        <tr>
          <td>${row.asset_id}</td>
          <td>${row.asset_unique_id}</td>
          <td>${row.asset_name}</td>
          <td>${row.category || ""}</td>
          <td><span class="${getStatusBadgeClass(row.status)}">${row.status}</span></td>
          <td>${row.asset_location || ""}</td>
          <td>
            ${
              isAdmin()
                ? `<div class='actions'><button onclick='openAssetModal(${JSON.stringify(row)})'>Edit</button>
                   <button class='danger' onclick='deleteAsset(${row.id})'>Deactivate</button></div>`
                : "View Only"
            }
          </td>
        </tr>`
      )
      .join("");
  } catch (err) {
    showToast(err.message, "error");
  }
}

function openAssetModal(data = null) {
  if (!isAdmin()) return;
  const modal = document.getElementById("assetModal");
  const form = document.getElementById("assetForm");
  form.reset();
  editingAssetId = null;

  if (data) {
    editingAssetId = data.id;
    Object.keys(data).forEach((key) => {
      const input = form.elements[key];
      if (input) input.value = data[key] || "";
    });
    document.getElementById("assetModalTitle").textContent = "Edit Asset";
  } else {
    document.getElementById("assetModalTitle").textContent = "Add Asset";
  }

  modal.classList.add("open");
}

function closeAssetModal() {
  document.getElementById("assetModal").classList.remove("open");
}

async function saveAsset(e) {
  e.preventDefault();
  try {
    const formData = new FormData(e.target);
    const payload = Object.fromEntries(formData.entries());

    Object.keys(payload).forEach((k) => {
      if (payload[k] === "") payload[k] = null;
    });

    if (editingAssetId) {
      await apiRequest(`/api/assets/${editingAssetId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      showToast("Asset updated", "success");
    } else {
      await apiRequest("/api/assets", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      showToast("Asset created", "success");
    }

    closeAssetModal();
    loadAssets();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function deleteAsset(id) {
  if (!confirm("Deactivate this asset?")) return;
  try {
    await apiRequest(`/api/assets/${id}`, { method: "DELETE" });
    showToast("Asset deactivated", "info");
    loadAssets();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function exportAssets() {
  try {
    const format = document.getElementById("assetExportFormat")?.value || "csv";
    const ext = format === "excel" ? "xlsx" : "csv";
    await downloadFile(`/api/assets/export?fmt=${format}`, `assets.${ext}`);
    showToast("Assets exported", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

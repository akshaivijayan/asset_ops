if (window.location.pathname.endsWith("dashboard.html") || window.location.pathname === "/dashboard.html") {
  requireAuth();
}

async function loadDashboard() {
  const statsEl = document.getElementById("stats");
  if (!statsEl) return;

  const stats = await apiRequest("/api/reports/dashboard");
  const cards = [
    ["Total Employees", stats.total_employees],
    ["Total Assets", stats.total_assets],
    ["Assigned Assets", stats.assigned_assets],
    ["Available Assets", stats.available_assets],
    ["Under Repair", stats.under_repair_assets],
  ];

  statsEl.innerHTML = cards
    .map(([label, value]) => `<div class="card"><div class="label">${label}</div><div class="value">${value}</div></div>`)
    .join("");

  const recent = await apiRequest("/api/reports/recent-assignments");
  const body = document.getElementById("recentAssignments");
  if (!recent.length) {
    renderEmptyRow("recentAssignments", 5, "No recent assignments");
    return;
  }

  body.innerHTML = recent
    .map(
      (row) => `
      <tr>
        <td>${row.assignment_id || ""}</td>
        <td>${row.asset_name || ""} (${row.asset_unique_id || ""})</td>
        <td>${row.employee_name || ""}</td>
        <td>${row.assigned_date || ""}</td>
        <td><span class="${getStatusBadgeClass(row.status)}">${row.status || ""}</span></td>
      </tr>`
    )
    .join("");
}

async function loadOnboardAssets() {
  const select = document.getElementById("onboardAssetSelect");
  if (!select) return;
  const assets = await apiRequest("/api/assets?status=Available&limit=200");
  if (!assets.length) {
    select.innerHTML = "<option value=''>No available assets</option>";
    return;
  }
  select.innerHTML = assets
    .map((a) => `<option value="${a.id}">${a.asset_unique_id} - ${a.asset_name} (${a.category || "Uncategorized"})</option>`)
    .join("");
}

async function loadOffboardEmployees() {
  const select = document.getElementById("offboardEmployeeSelect");
  if (!select) return;
  const employees = await apiRequest("/api/employees?limit=500");
  const active = employees.filter((e) => e.employment_status === "Active");
  if (!active.length) {
    select.innerHTML = "<option value=''>No active employees</option>";
    return;
  }
  select.innerHTML = active
    .map((e) => `<option value="${e.id}">${e.employee_id} - ${e.name}</option>`)
    .join("");
}

function openOnboardModal() {
  if (!isAdmin()) return;
  document.getElementById("onboardForm")?.reset();
  document.getElementById("onboardModal")?.classList.add("open");
  loadOnboardAssets().catch((err) => showToast(err.message, "error"));
}

function closeOnboardModal() {
  document.getElementById("onboardModal")?.classList.remove("open");
}

function openOffboardModal() {
  if (!isAdmin()) return;
  document.getElementById("offboardForm")?.reset();
  document.getElementById("offboardModal")?.classList.add("open");
  loadOffboardEmployees().catch((err) => showToast(err.message, "error"));
}

function closeOffboardModal() {
  document.getElementById("offboardModal")?.classList.remove("open");
}

async function submitOnboard(e) {
  e.preventDefault();
  try {
    const form = e.target;
    const payload = Object.fromEntries(new FormData(form).entries());

    const select = document.getElementById("onboardAssetSelect");
    payload.asset_ids = Array.from(select.selectedOptions)
      .map((opt) => Number(opt.value))
      .filter((id) => Number.isFinite(id));

    Object.keys(payload).forEach((k) => {
      if (payload[k] === "") payload[k] = null;
    });

    await apiRequest("/api/employees/onboard", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    showToast("Employee added and assets assigned", "success");
    closeOnboardModal();
    await loadDashboard();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function submitOffboard(e) {
  e.preventDefault();
  try {
    const confirm = document.getElementById("offboardConfirm");
    if (!confirm?.checked) {
      showToast("Please confirm employee removal", "info");
      return;
    }

    const form = e.target;
    const data = Object.fromEntries(new FormData(form).entries());
    const payload = {
      employee_id: Number(data.employee_id),
      notes: data.notes || null,
      confirm: true,
    };

    await apiRequest("/api/employees/offboard", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    showToast("Employee removed and assets returned", "success");
    closeOffboardModal();
    await loadDashboard();
  } catch (err) {
    showToast(err.message, "error");
  }
}

function initLifecycleActions() {
  const onboardBtn = document.getElementById("openOnboardBtn");
  const offboardBtn = document.getElementById("openOffboardBtn");
  const onboardForm = document.getElementById("onboardForm");
  const offboardForm = document.getElementById("offboardForm");

  if (!onboardBtn || !offboardBtn || !onboardForm || !offboardForm) return;

  if (!isAdmin()) {
    onboardBtn.classList.add("hidden");
    offboardBtn.classList.add("hidden");
    return;
  }

  onboardBtn.addEventListener("click", openOnboardModal);
  offboardBtn.addEventListener("click", openOffboardModal);
  onboardForm.addEventListener("submit", submitOnboard);
  offboardForm.addEventListener("submit", submitOffboard);
}

initLifecycleActions();
loadDashboard().catch((err) => showToast(err.message, "error"));

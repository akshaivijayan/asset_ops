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

loadDashboard().catch((err) => showToast(err.message, "error"));

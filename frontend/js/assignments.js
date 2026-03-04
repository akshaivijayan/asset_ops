if (document.getElementById("assignmentRows")) {
  requireAuth();
  if (!isAdmin()) {
    document.getElementById("addAssignmentBtn").classList.add("hidden");
  }
  loadAssignments();
  document.getElementById("addAssignmentBtn")?.addEventListener("click", openAssignmentModal);
  document.getElementById("assignmentForm").addEventListener("submit", saveAssignment);
}

async function loadAssignments() {
  try {
    const status = document.getElementById("statusFilter").value;
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    const rows = await apiRequest(`/api/assignments${query}`);
    const body = document.getElementById("assignmentRows");

    if (!rows.length) {
      renderEmptyRow("assignmentRows", 7, "No assignments found.");
      return;
    }

    body.innerHTML = rows
      .map(
        (row) => `
        <tr>
          <td>${row.assignment_id}</td>
          <td>${row.asset_name || ""} (${row.asset_unique_id || ""})</td>
          <td>${row.employee_name || ""}</td>
          <td>${row.assigned_date || ""}</td>
          <td>${row.returned_date || ""}</td>
          <td><span class="${getStatusBadgeClass(row.assignment_status)}">${row.assignment_status}</span></td>
          <td>
            ${isAdmin() && row.assignment_status === "Assigned" ? `<button onclick='returnAsset(${row.id})'>Return</button>` : "-"}
          </td>
        </tr>`
      )
      .join("");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function openAssignmentModal() {
  if (!isAdmin()) return;
  try {
    const [assets, employees] = await Promise.all([
      apiRequest("/api/assets?status=Available"),
      apiRequest("/api/employees"),
    ]);

    const assetSelect = document.getElementById("assetSelect");
    const employeeSelect = document.getElementById("employeeSelect");

    if (!assets.length) {
      showToast("No available assets for assignment", "info");
      return;
    }

    assetSelect.innerHTML = assets
      .map((a) => `<option value='${a.id}'>${a.asset_unique_id} - ${a.asset_name}</option>`)
      .join("");
    employeeSelect.innerHTML = employees
      .filter((e) => e.employment_status === "Active")
      .map((e) => `<option value='${e.id}'>${e.employee_id} - ${e.name}</option>`)
      .join("");

    document.querySelector("#assignmentForm [name='assigned_date']").value = new Date().toISOString().slice(0, 10);
    document.getElementById("assignmentModal").classList.add("open");
  } catch (err) {
    showToast(err.message, "error");
  }
}

function closeAssignmentModal() {
  document.getElementById("assignmentModal").classList.remove("open");
}

async function saveAssignment(e) {
  e.preventDefault();
  try {
    const payload = Object.fromEntries(new FormData(e.target).entries());
    payload.asset_id = Number(payload.asset_id);
    payload.employee_id = Number(payload.employee_id);

    await apiRequest("/api/assignments", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    showToast("Asset assigned successfully", "success");
    closeAssignmentModal();
    loadAssignments();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function returnAsset(id) {
  const returned_date = prompt("Enter return date (YYYY-MM-DD)", new Date().toISOString().slice(0, 10));
  if (!returned_date) return;

  try {
    await apiRequest(`/api/assignments/${id}/return`, {
      method: "PUT",
      body: JSON.stringify({ returned_date }),
    });

    showToast("Asset marked as returned", "success");
    loadAssignments();
  } catch (err) {
    showToast(err.message, "error");
  }
}

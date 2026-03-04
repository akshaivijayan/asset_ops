let editingEmployeeId = null;

if (document.getElementById("employeeRows")) {
  requireAuth();
  if (!isAdmin()) {
    document.getElementById("addEmployeeBtn").classList.add("hidden");
  }
  loadEmployees();

  document.getElementById("addEmployeeBtn")?.addEventListener("click", () => openEmployeeModal());
  document.getElementById("employeeForm").addEventListener("submit", saveEmployee);
}

async function loadEmployees() {
  try {
    const params = new URLSearchParams();
    ["search", "designation", "department"].forEach((id) => {
      const value = document.getElementById(id).value.trim();
      if (value) params.append(id, value);
    });

    const rows = await apiRequest(`/api/employees?${params.toString()}`);
    const body = document.getElementById("employeeRows");

    if (!rows.length) {
      renderEmptyRow("employeeRows", 7, "No employees matched your filters.");
      return;
    }

    body.innerHTML = rows
      .map(
        (row) => `
        <tr>
          <td>${row.employee_id}</td>
          <td>${row.name}</td>
          <td>${row.email}</td>
          <td>${row.department || ""}</td>
          <td>${row.designation || ""}</td>
          <td><span class="${getStatusBadgeClass(row.employment_status)}">${row.employment_status}</span></td>
          <td>
            ${
              isAdmin()
                ? `<div class='actions'><button onclick='openEmployeeModal(${JSON.stringify(row)})'>Edit</button>
                   <button class='danger' onclick='deleteEmployee(${row.id})'>Deactivate</button></div>`
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

function openEmployeeModal(data = null) {
  if (!isAdmin()) return;
  const modal = document.getElementById("employeeModal");
  const form = document.getElementById("employeeForm");
  form.reset();
  editingEmployeeId = null;

  if (data) {
    editingEmployeeId = data.id;
    Object.keys(data).forEach((key) => {
      const input = form.elements[key];
      if (input) input.value = data[key] || "";
    });
    document.getElementById("employeeModalTitle").textContent = "Edit Employee";
  } else {
    document.getElementById("employeeModalTitle").textContent = "Add Employee";
  }

  modal.classList.add("open");
}

function closeEmployeeModal() {
  document.getElementById("employeeModal").classList.remove("open");
}

async function saveEmployee(e) {
  e.preventDefault();
  try {
    const formData = new FormData(e.target);
    const payload = Object.fromEntries(formData.entries());

    Object.keys(payload).forEach((k) => {
      if (payload[k] === "") payload[k] = null;
    });

    if (editingEmployeeId) {
      await apiRequest(`/api/employees/${editingEmployeeId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      showToast("Employee updated", "success");
    } else {
      await apiRequest("/api/employees", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      showToast("Employee created", "success");
    }

    closeEmployeeModal();
    loadEmployees();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function deleteEmployee(id) {
  if (!confirm("Deactivate this employee?")) return;
  try {
    await apiRequest(`/api/employees/${id}`, { method: "DELETE" });
    showToast("Employee deactivated", "info");
    loadEmployees();
  } catch (err) {
    showToast(err.message, "error");
  }
}

const API_BASE = "";
const IS_GH_PAGES = window.location.hostname.endsWith("github.io");

const DEMO_STORAGE_KEY = "asset_ops_demo_db_v1";

function getToken() {
  return localStorage.getItem("token") || "";
}

function getRole() {
  return localStorage.getItem("role") || "";
}

function safeJsonParse(value, fallback) {
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

function seedDemoDb() {
  const today = new Date().toISOString().slice(0, 10);
  return {
    users: [
      { id: 1, name: "IT Admin", email: "admin@company.com", password: "Admin@123", role: "admin" },
      { id: 2, name: "CEO", email: "ceo@company.com", password: "Viewer@123", role: "viewer" },
    ],
    employees: [
      { id: 1, employee_id: "EMP-0001", name: "Arun Nair", email: "arun@company.com", phone: "0500000001", designation: "Facilities Lead", department: "Operations", reporting_person: "COO", office_location: "Head Office", joining_date: "2024-02-01", employment_status: "Active", notes: "Manages office equipment", is_deleted: false },
      { id: 2, employee_id: "EMP-0002", name: "Sara Joseph", email: "sara@company.com", phone: "0500000002", designation: "Accountant", department: "Accounts", reporting_person: "Finance Manager", office_location: "Regional Office", joining_date: "2023-11-12", employment_status: "Active", notes: "", is_deleted: false },
    ],
    assets: [
      { id: 1, asset_id: "AST-00001", asset_unique_id: "LAP-HQ-001", asset_name: "Dell Latitude", category: "Laptop", brand: "Dell", model: "7420", serial_number: "SN001", purchase_date: "2024-01-10", purchase_cost: 4200, vendor: "Tech Gulf", warranty_expiry: "2026-12-30", asset_location: "Head Office", status: "Assigned", is_deleted: false },
      { id: 2, asset_id: "AST-00002", asset_unique_id: "MON-HQ-002", asset_name: "Samsung Monitor", category: "Monitor", brand: "Samsung", model: "S24", serial_number: "SN002", purchase_date: "2024-03-08", purchase_cost: 780, vendor: "Office Mart", warranty_expiry: "2027-03-07", asset_location: "Head Office", status: "Available", is_deleted: false },
      { id: 3, asset_id: "AST-00003", asset_unique_id: "TAB-REG-003", asset_name: "iPad", category: "Tablet", brand: "Apple", model: "Air", serial_number: "SN003", purchase_date: "2024-06-02", purchase_cost: 2500, vendor: "Apple Reseller", warranty_expiry: "2026-06-01", asset_location: "Regional Office", status: "Under Repair", is_deleted: false },
    ],
    assignments: [
      { id: 1, assignment_id: "ASN-00001", asset_id: 1, employee_id: 1, assigned_date: today, returned_date: null, assignment_status: "Assigned", notes: "Initial issue" },
    ],
  };
}

function loadDemoDb() {
  const existing = localStorage.getItem(DEMO_STORAGE_KEY);
  if (!existing) {
    const seeded = seedDemoDb();
    localStorage.setItem(DEMO_STORAGE_KEY, JSON.stringify(seeded));
    return seeded;
  }
  return safeJsonParse(existing, seedDemoDb());
}

function saveDemoDb(db) {
  localStorage.setItem(DEMO_STORAGE_KEY, JSON.stringify(db));
}

function parsePath(path) {
  const [pathname, query = ""] = path.split("?");
  return { pathname, query: new URLSearchParams(query) };
}

function nextCode(prefix, count, pad) {
  return `${prefix}${String(count + 1).padStart(pad, "0")}`;
}

function withAssignmentDetails(db, assignment) {
  const asset = db.assets.find((a) => a.id === assignment.asset_id);
  const employee = db.employees.find((e) => e.id === assignment.employee_id);
  return {
    ...assignment,
    asset_name: asset?.asset_name || null,
    asset_unique_id: asset?.asset_unique_id || null,
    employee_name: employee?.name || null,
    employee_code: employee?.employee_id || null,
  };
}

function filterContains(value, needle) {
  if (!needle) return true;
  return String(value || "").toLowerCase().includes(String(needle).toLowerCase());
}

function toCsv(rows) {
  if (!rows.length) return "";
  const keys = Object.keys(rows[0]);
  const lines = [keys.join(",")];
  rows.forEach((row) => {
    lines.push(keys.map((k) => `"${String(row[k] ?? "").replaceAll('"', '""')}"`).join(","));
  });
  return lines.join("\n");
}

function getDemoReport(db, reportName) {
  if (reportName === "assets-by-employee") {
    return db.assignments
      .filter((a) => a.assignment_status === "Assigned")
      .map((a) => {
        const asset = db.assets.find((x) => x.id === a.asset_id);
        const employee = db.employees.find((x) => x.id === a.employee_id);
        return {
          employee_id: employee?.employee_id || "",
          employee_name: employee?.name || "",
          department: employee?.department || "",
          asset_id: asset?.asset_id || "",
          asset_unique_id: asset?.asset_unique_id || "",
          asset_name: asset?.asset_name || "",
          category: asset?.category || "",
          assigned_date: a.assigned_date,
        };
      });
  }

  if (reportName === "unassigned-assets") {
    return db.assets
      .filter((a) => a.status === "Available" && !a.is_deleted)
      .map((a) => ({
        asset_id: a.asset_id,
        asset_unique_id: a.asset_unique_id,
        asset_name: a.asset_name,
        category: a.category,
        location: a.asset_location,
        status: a.status,
      }));
  }

  if (reportName === "under-repair") {
    return db.assets
      .filter((a) => a.status === "Under Repair" && !a.is_deleted)
      .map((a) => ({
        asset_id: a.asset_id,
        asset_unique_id: a.asset_unique_id,
        asset_name: a.asset_name,
        location: a.asset_location,
        vendor: a.vendor,
      }));
  }

  if (reportName === "warranty-expiring") {
    const now = new Date();
    const days30 = new Date(now.getTime() + 30 * 86400000);
    return db.assets
      .filter((a) => {
        if (!a.warranty_expiry || a.is_deleted) return false;
        const dt = new Date(a.warranty_expiry);
        return dt >= now && dt <= days30;
      })
      .map((a) => ({
        asset_id: a.asset_id,
        asset_unique_id: a.asset_unique_id,
        asset_name: a.asset_name,
        warranty_expiry: a.warranty_expiry,
        vendor: a.vendor,
      }));
  }

  return [];
}

function getDemoEmployees(db) {
  return db.employees
    .filter((e) => !e.is_deleted)
    .map((e) => ({
      employee_id: e.employee_id,
      name: e.name,
      email: e.email,
      phone: e.phone || "",
      designation: e.designation || "",
      department: e.department || "",
      reporting_person: e.reporting_person || "",
      office_location: e.office_location || "",
      joining_date: e.joining_date || "",
      employment_status: e.employment_status || "",
      notes: e.notes || "",
    }));
}

function getDemoAssets(db) {
  return db.assets
    .filter((a) => !a.is_deleted)
    .map((a) => ({
      asset_id: a.asset_id,
      asset_unique_id: a.asset_unique_id,
      asset_name: a.asset_name,
      category: a.category || "",
      brand: a.brand || "",
      model: a.model || "",
      serial_number: a.serial_number || "",
      purchase_date: a.purchase_date || "",
      purchase_cost: a.purchase_cost || "",
      vendor: a.vendor || "",
      warranty_expiry: a.warranty_expiry || "",
      asset_location: a.asset_location || "",
      status: a.status || "",
    }));
}

async function demoApi(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const body = options.body ? safeJsonParse(options.body, {}) : {};
  const { pathname, query } = parsePath(path);
  const db = loadDemoDb();

  if (pathname === "/api/auth/login" && method === "POST") {
    const user = db.users.find((u) => u.email.toLowerCase() === String(body.email || "").toLowerCase() && u.password === body.password);
    if (!user) throw new Error("Invalid email or password");
    return { access_token: "demo-token", token_type: "bearer", role: user.role, name: user.name };
  }

  if (pathname === "/api/employees" && method === "GET") {
    let rows = db.employees.filter((e) => !e.is_deleted);
    rows = rows.filter((e) => filterContains(e.name, query.get("search")) || filterContains(e.email, query.get("search")) || filterContains(e.employee_id, query.get("search")));
    if (query.get("designation")) rows = rows.filter((e) => filterContains(e.designation, query.get("designation")));
    if (query.get("department")) rows = rows.filter((e) => filterContains(e.department, query.get("department")));
    return rows;
  }

  if (pathname === "/api/employees" && method === "POST") {
    const id = Math.max(0, ...db.employees.map((e) => e.id)) + 1;
    const row = { id, employee_id: nextCode("EMP-", db.employees.length, 4), is_deleted: false, ...body };
    db.employees.push(row);
    saveDemoDb(db);
    return row;
  }

  if (pathname === "/api/employees/onboard" && method === "POST") {
    const exists = db.employees.find((e) => String(e.email || "").toLowerCase() === String(body.email || "").toLowerCase());
    if (exists) throw new Error("Employee email already exists");

    const assetIds = Array.isArray(body.asset_ids) ? body.asset_ids.map((x) => Number(x)) : [];
    const selectedAssets = db.assets.filter((a) => assetIds.includes(a.id));
    if (selectedAssets.some((a) => a.status !== "Available" || a.is_deleted)) {
      throw new Error("One or more selected assets are not available");
    }

    const employeeId = Math.max(0, ...db.employees.map((e) => e.id)) + 1;
    const employee = {
      id: employeeId,
      employee_id: nextCode("EMP-", db.employees.length, 4),
      is_deleted: false,
      name: body.name,
      email: body.email,
      phone: body.phone || null,
      designation: body.designation || null,
      department: body.department || null,
      reporting_person: body.reporting_person || null,
      office_location: body.office_location || null,
      joining_date: body.joining_date || null,
      employment_status: body.employment_status || "Active",
      notes: body.notes || null,
    };
    db.employees.push(employee);

    let assignedCount = 0;
    if (employee.employment_status === "Active") {
      selectedAssets.forEach((asset) => {
        const asnId = Math.max(0, ...db.assignments.map((a) => a.id)) + 1;
        const assignment = {
          id: asnId,
          assignment_id: nextCode("ASN-", db.assignments.length, 5),
          asset_id: asset.id,
          employee_id: employee.id,
          assigned_date: new Date().toISOString().slice(0, 10),
          returned_date: null,
          assignment_status: "Assigned",
          notes: body.assignment_notes || null,
        };
        db.assignments.push(assignment);
        asset.status = "Assigned";
        assignedCount += 1;
      });
    }

    saveDemoDb(db);
    return {
      message: "Employee onboarded successfully",
      employee_id: employee.id,
      employee_code: employee.employee_id,
      assigned_assets: assignedCount,
    };
  }

  if (pathname === "/api/employees/offboard" && method === "POST") {
    if (!body.confirm) throw new Error("Confirmation is required");
    const employeeId = Number(body.employee_id);
    const employee = db.employees.find((e) => e.id === employeeId && !e.is_deleted);
    if (!employee) throw new Error("Employee not found");

    const activeAssignments = db.assignments.filter(
      (a) => a.employee_id === employee.id && a.assignment_status === "Assigned"
    );
    activeAssignments.forEach((assignment) => {
      assignment.assignment_status = "Returned";
      assignment.returned_date = new Date().toISOString().slice(0, 10);
      if (body.notes) assignment.notes = body.notes;
      const asset = db.assets.find((a) => a.id === assignment.asset_id);
      if (asset && asset.status === "Assigned") asset.status = "Available";
    });

    employee.employment_status = "Inactive";
    employee.is_deleted = true;
    saveDemoDb(db);
    return {
      message: "Employee offboarded successfully",
      employee_id: employee.id,
      employee_code: employee.employee_id,
      returned_assets: activeAssignments.length,
    };
  }

  const employeeMatch = pathname.match(/^\/api\/employees\/(\d+)$/);
  if (employeeMatch && method === "PUT") {
    const id = Number(employeeMatch[1]);
    const row = db.employees.find((e) => e.id === id && !e.is_deleted);
    if (!row) throw new Error("Employee not found");
    Object.assign(row, body);
    saveDemoDb(db);
    return row;
  }
  if (employeeMatch && method === "DELETE") {
    const id = Number(employeeMatch[1]);
    const row = db.employees.find((e) => e.id === id && !e.is_deleted);
    if (!row) throw new Error("Employee not found");
    row.employment_status = "Inactive";
    row.is_deleted = true;
    saveDemoDb(db);
    return { message: "Employee deactivated" };
  }

  if (pathname === "/api/assets" && method === "GET") {
    let rows = db.assets.filter((a) => !a.is_deleted);
    const search = query.get("search");
    if (search) rows = rows.filter((a) => filterContains(a.asset_id, search) || filterContains(a.asset_unique_id, search) || filterContains(a.asset_name, search));
    if (query.get("category")) rows = rows.filter((a) => filterContains(a.category, query.get("category")));
    if (query.get("status")) rows = rows.filter((a) => a.status === query.get("status"));
    if (query.get("assigned_employee")) {
      const term = query.get("assigned_employee");
      rows = rows.filter((a) => {
        const asn = db.assignments.find((x) => x.asset_id === a.id && x.assignment_status === "Assigned");
        if (!asn) return false;
        const emp = db.employees.find((e) => e.id === asn.employee_id);
        return filterContains(emp?.name, term);
      });
    }
    return rows;
  }

  if (pathname === "/api/assets" && method === "POST") {
    if (db.assets.some((a) => a.asset_unique_id === body.asset_unique_id)) throw new Error("Asset unique ID already exists");
    const id = Math.max(0, ...db.assets.map((a) => a.id)) + 1;
    const row = { id, asset_id: nextCode("AST-", db.assets.length, 5), is_deleted: false, ...body };
    db.assets.push(row);
    saveDemoDb(db);
    return row;
  }

  const assetMatch = pathname.match(/^\/api\/assets\/(\d+)$/);
  if (assetMatch && method === "PUT") {
    const id = Number(assetMatch[1]);
    const row = db.assets.find((a) => a.id === id && !a.is_deleted);
    if (!row) throw new Error("Asset not found");
    Object.assign(row, body);
    saveDemoDb(db);
    return row;
  }
  if (assetMatch && method === "DELETE") {
    const id = Number(assetMatch[1]);
    const row = db.assets.find((a) => a.id === id && !a.is_deleted);
    if (!row) throw new Error("Asset not found");
    row.is_deleted = true;
    row.status = "Inactive";
    saveDemoDb(db);
    return { message: "Asset deactivated" };
  }

  if (pathname === "/api/assignments" && method === "GET") {
    let rows = db.assignments;
    if (query.get("status")) rows = rows.filter((x) => x.assignment_status === query.get("status"));
    return rows.map((r) => withAssignmentDetails(db, r));
  }

  if (pathname === "/api/assignments" && method === "POST") {
    const asset = db.assets.find((a) => a.id === Number(body.asset_id) && !a.is_deleted);
    if (!asset) throw new Error("Asset not found");
    if (asset.status !== "Available") throw new Error("Only available assets can be assigned");

    const employee = db.employees.find((e) => e.id === Number(body.employee_id) && !e.is_deleted);
    if (!employee) throw new Error("Employee not found");

    const id = Math.max(0, ...db.assignments.map((a) => a.id)) + 1;
    const row = {
      id,
      assignment_id: nextCode("ASN-", db.assignments.length, 5),
      asset_id: Number(body.asset_id),
      employee_id: Number(body.employee_id),
      assigned_date: body.assigned_date,
      returned_date: null,
      assignment_status: "Assigned",
      notes: body.notes || null,
    };
    db.assignments.push(row);
    asset.status = "Assigned";
    saveDemoDb(db);
    return withAssignmentDetails(db, row);
  }

  const returnMatch = pathname.match(/^\/api\/assignments\/(\d+)\/return$/);
  if (returnMatch && method === "PUT") {
    const id = Number(returnMatch[1]);
    const row = db.assignments.find((a) => a.id === id);
    if (!row) throw new Error("Assignment not found");
    row.returned_date = body.returned_date;
    row.assignment_status = "Returned";
    if (body.notes) row.notes = body.notes;
    const asset = db.assets.find((a) => a.id === row.asset_id);
    if (asset) asset.status = "Available";
    saveDemoDb(db);
    return withAssignmentDetails(db, row);
  }

  if (pathname === "/api/reports/dashboard" && method === "GET") {
    return {
      total_employees: db.employees.filter((e) => !e.is_deleted).length,
      total_assets: db.assets.filter((a) => !a.is_deleted).length,
      assigned_assets: db.assets.filter((a) => a.status === "Assigned" && !a.is_deleted).length,
      available_assets: db.assets.filter((a) => a.status === "Available" && !a.is_deleted).length,
      under_repair_assets: db.assets.filter((a) => a.status === "Under Repair" && !a.is_deleted).length,
    };
  }

  if (pathname === "/api/reports/recent-assignments" && method === "GET") {
    return db.assignments.slice().reverse().slice(0, 10).map((a) => {
      const d = withAssignmentDetails(db, a);
      return {
        assignment_id: d.assignment_id,
        asset_name: d.asset_name,
        asset_unique_id: d.asset_unique_id,
        employee_name: d.employee_name,
        assigned_date: d.assigned_date,
        status: d.assignment_status,
      };
    });
  }

  if (pathname === "/api/reports/assets-by-employee" && method === "GET") return getDemoReport(db, "assets-by-employee");
  if (pathname === "/api/reports/unassigned-assets" && method === "GET") return getDemoReport(db, "unassigned-assets");
  if (pathname === "/api/reports/under-repair" && method === "GET") return getDemoReport(db, "under-repair");
  if (pathname === "/api/reports/warranty-expiring" && method === "GET") return getDemoReport(db, "warranty-expiring");

  if (pathname.startsWith("/api/reports/import/") && method === "POST") {
    return { message: "Demo mode: import is disabled on GitHub Pages" };
  }

  throw new Error(`Demo API route not implemented: ${method} ${pathname}`);
}

async function apiRequest(path, options = {}) {
  if (IS_GH_PAGES) {
    return demoApi(path, options);
  }

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
  if (IS_GH_PAGES) {
    const db = loadDemoDb();
    const reportMatch = path.match(/\/api\/reports\/export\/([^?]+)(\?.*)?$/);
    const employeeMatch = path.match(/\/api\/employees\/export(\?.*)?$/);
    const assetMatch = path.match(/\/api\/assets\/export(\?.*)?$/);

    let fmt = "csv";
    let rows = [];
    if (reportMatch) {
      const reportName = reportMatch[1];
      const query = new URLSearchParams((reportMatch[2] || "").replace("?", ""));
      fmt = query.get("fmt") || "csv";
      rows = getDemoReport(db, reportName);
    } else if (employeeMatch) {
      const query = new URLSearchParams((employeeMatch[1] || "").replace("?", ""));
      fmt = query.get("fmt") || "csv";
      rows = getDemoEmployees(db);
    } else if (assetMatch) {
      const query = new URLSearchParams((assetMatch[1] || "").replace("?", ""));
      fmt = query.get("fmt") || "csv";
      rows = getDemoAssets(db);
    } else {
      throw new Error("Invalid export path");
    }

    if (fmt === "excel") {
      // CSV content saved as .xlsx for preview-only demo mode.
      const blob = new Blob([toCsv(rows)], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      return;
    }

    const blob = new Blob([toCsv(rows)], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    return;
  }

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


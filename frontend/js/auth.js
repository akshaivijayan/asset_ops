function logout() {
  localStorage.clear();
  window.location.href = "index.html";
}

function requireAuth() {
  const token = localStorage.getItem("token");
  if (!token) {
    window.location.href = "index.html";
    return false;
  }
  return true;
}

function isAdmin() {
  return getRole() === "admin";
}

const loginForm = document.getElementById("loginForm");
if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const errorEl = document.getElementById("loginError");

    try {
      const data = await apiRequest("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("role", data.role);
      localStorage.setItem("name", data.name);
      window.location.href = "dashboard.html";
    } catch (err) {
      errorEl.textContent = err.message;
    }
  });
}

const userBadge = document.getElementById("userBadge");
if (userBadge) {
  requireAuth();
  userBadge.textContent = `${localStorage.getItem("name") || "User"} (${getRole()})`;
}

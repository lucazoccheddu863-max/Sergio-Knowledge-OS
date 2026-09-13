const endpoints = {
  status: "/api/v1/status",
  health: "/api/v1/health",
  engines: "/api/v1/engines",
  security: "/api/v1/security/status",
};

const text = (id, value) => {
  document.getElementById(id).textContent = value;
};

const badge = (value) => {
  const ok = value === true || value === "healthy" || value === "operational";
  return `<strong class="badge ${ok ? "ok" : "warn"}">${String(value)}</strong>`;
};

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`);
  }
  return response.json();
}

async function refreshDashboard() {
  const [status, health, engines, security] = await Promise.all([
    getJson(endpoints.status),
    getJson(endpoints.health),
    getJson(endpoints.engines),
    getJson(endpoints.security),
  ]);

  text("system-status", status.status);
  text("system-version", status.version);
  text("system-milestone", status.milestone);
  text("security-status", security.enabled ? "Enabled" : "Open mode");

  document.getElementById("health-list").innerHTML = Object.entries(health.engines)
    .map(([name, value]) => `<div class="row"><span>${name}</span>${badge(value)}</div>`)
    .join("");

  document.getElementById("engine-list").innerHTML = engines.engines
    .map((engine) => `<span class="chip">${engine}</span>`)
    .join("");

  text("updated-at", new Date().toLocaleString());
}

document.getElementById("refresh").addEventListener("click", () => {
  refreshDashboard().catch((error) => {
    text("system-status", "Error");
    document.getElementById("health-list").innerHTML = `<div class="row"><span>${error.message}</span>${badge(false)}</div>`;
  });
});

refreshDashboard().catch((error) => {
  text("system-status", "Error");
  document.getElementById("health-list").innerHTML = `<div class="row"><span>${error.message}</span>${badge(false)}</div>`;
});

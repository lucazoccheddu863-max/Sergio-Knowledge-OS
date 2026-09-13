const endpoints = {
  status: "/api/v1/status",
  health: "/api/v1/health",
  engines: "/api/v1/engines",
  security: "/api/v1/security/status",
  readiness: "/api/v1/admin/readiness",
  backupManifest: "/api/v1/admin/backup/manifest",
  backupCreate: "/api/v1/admin/backup/create",
  backupInspect: "/api/v1/admin/backup/inspect",
  backupRestoreStage: "/api/v1/admin/backup/restore/stage",
};

const text = (id, value) => {
  document.getElementById(id).textContent = value;
};

const badge = (value) => {
  const ok = value === true || value === "healthy" || value === "operational" || value === "pass";
  return `<strong class="badge ${ok ? "ok" : "warn"}">${String(value)}</strong>`;
};

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`);
  }
  return response.json();
}

async function postJson(url) {
  const response = await fetch(url, { method: "POST" });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || `${url} returned ${response.status}`);
  }
  return data;
}

const setBackupRows = (rows) => {
  document.getElementById("backup-list").innerHTML = rows
    .map(([name, value]) => `<div class="row"><span>${name}</span><strong>${value}</strong></div>`)
    .join("");
};

async function refreshBackupManifest() {
  const manifest = await getJson(endpoints.backupManifest);
  text("backup-summary", manifest.ready ? "Ready" : "Needs attention");
  setBackupRows([
    ["Destination", manifest.destination],
    ["Files", manifest.total_files],
    ["Size", `${manifest.total_bytes} bytes`],
    ["Warnings", manifest.warnings.length ? manifest.warnings.join("; ") : "None"],
  ]);
}

async function refreshDashboard() {
  const [status, health, engines, security, readiness, backupManifest] = await Promise.all([
    getJson(endpoints.status),
    getJson(endpoints.health),
    getJson(endpoints.engines),
    getJson(endpoints.security),
    getJson(endpoints.readiness),
    getJson(endpoints.backupManifest),
  ]);

  text("system-status", status.status);
  text("system-version", status.version);
  text("system-milestone", status.milestone);
  text("security-status", security.enabled ? "Enabled" : "Open mode");

  document.getElementById("health-list").innerHTML = Object.entries(health.engines)
    .map(([name, value]) => `<div class="row"><span>${name}</span>${badge(value)}</div>`)
    .join("");

  text("readiness-summary", readiness.ready ? "Ready" : "Needs attention");
  document.getElementById("readiness-list").innerHTML = readiness.checks
    .map((check) => `<div class="row"><span>${check.name}: ${check.message}</span>${badge(check.status)}</div>`)
    .join("");

  document.getElementById("engine-list").innerHTML = engines.engines
    .map((engine) => `<span class="chip">${engine}</span>`)
    .join("");

  text("backup-summary", backupManifest.ready ? "Ready" : "Needs attention");
  setBackupRows([
    ["Destination", backupManifest.destination],
    ["Files", backupManifest.total_files],
    ["Size", `${backupManifest.total_bytes} bytes`],
    ["Warnings", backupManifest.warnings.length ? backupManifest.warnings.join("; ") : "None"],
  ]);

  text("updated-at", new Date().toLocaleString());
}

document.getElementById("refresh").addEventListener("click", () => {
  refreshDashboard().catch((error) => {
    text("system-status", "Error");
    document.getElementById("health-list").innerHTML = `<div class="row"><span>${error.message}</span>${badge(false)}</div>`;
    document.getElementById("readiness-list").innerHTML = "";
  });
});

document.getElementById("backup-create").addEventListener("click", () => {
  postJson(endpoints.backupCreate)
    .then((result) => {
      document.getElementById("backup-archive-path").value = result.archive_path;
      text("backup-summary", "Created");
      setBackupRows([
        ["Archive", result.archive_path],
        ["Files", result.manifest.total_files],
        ["Size", `${result.manifest.total_bytes} bytes`],
      ]);
    })
    .catch((error) => {
      text("backup-summary", "Error");
      setBackupRows([["Error", error.message]]);
    });
});

document.getElementById("backup-inspect").addEventListener("click", () => {
  const archivePath = document.getElementById("backup-archive-path").value.trim();
  if (!archivePath) {
    text("backup-summary", "Missing archive path");
    return;
  }
  getJson(`${endpoints.backupInspect}?archive_path=${encodeURIComponent(archivePath)}`)
    .then((inspection) => {
      text("backup-summary", inspection.ready ? "Archive ready" : "Archive warning");
      setBackupRows([
        ["Archive", inspection.archive_path],
        ["Entries", inspection.entries.length],
        ["Warnings", inspection.warnings.length ? inspection.warnings.join("; ") : "None"],
      ]);
    })
    .catch((error) => {
      text("backup-summary", "Error");
      setBackupRows([["Error", error.message]]);
    });
});

document.getElementById("backup-restore").addEventListener("click", () => {
  const archivePath = document.getElementById("backup-archive-path").value.trim();
  const targetDir = document.getElementById("backup-restore-target").value.trim();
  if (!archivePath || !targetDir) {
    text("backup-summary", "Missing restore input");
    return;
  }
  const params = new URLSearchParams({ archive_path: archivePath, target_dir: targetDir });
  postJson(`${endpoints.backupRestoreStage}?${params.toString()}`)
    .then((restore) => {
      text("backup-summary", "Restore staged");
      setBackupRows([
        ["Target", restore.target_dir],
        ["Extracted files", restore.extracted_files.length],
        ["Archive", restore.archive_path],
      ]);
    })
    .catch((error) => {
      text("backup-summary", "Error");
      setBackupRows([["Error", error.message]]);
    });
});

refreshDashboard().catch((error) => {
  text("system-status", "Error");
  document.getElementById("health-list").innerHTML = `<div class="row"><span>${error.message}</span>${badge(false)}</div>`;
  document.getElementById("readiness-list").innerHTML = "";
  refreshBackupManifest().catch(() => {
    text("backup-summary", "Error");
  });
});

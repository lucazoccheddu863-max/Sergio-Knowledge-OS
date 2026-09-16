const endpoints = {
  status: "/api/v1/status",
  health: "/api/v1/health",
  engines: "/api/v1/engines",
  security: "/api/v1/security/status",
  overview: "/api/v1/admin/overview",
  smoke: "/api/v1/admin/smoke",
  readiness: "/api/v1/admin/readiness",
  release: "/api/v1/admin/release",
  releasePackage: "/api/v1/admin/release/package",
  releasePackageInspect: "/api/v1/admin/release/package/inspect",
  releaseGate: "/api/v1/admin/release/gate",
  localLaunch: "/api/v1/admin/local/launch",
  localBootstrap: "/api/v1/admin/local/bootstrap",
  manual: "/api/v1/admin/manual",
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

const setReleasePackageRows = (rows) => {
  document.getElementById("release-package-list").innerHTML = rows
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
  const [status, health, engines, security, overview, smoke, launch, manual] = await Promise.all([
    getJson(endpoints.status),
    getJson(endpoints.health),
    getJson(endpoints.engines),
    getJson(endpoints.security),
    getJson(endpoints.overview),
    getJson(endpoints.smoke),
    getJson(endpoints.localLaunch),
    getJson(endpoints.manual),
  ]);
  const { release, readiness, backup: backupManifest } = overview;

  text("system-status", release.status || status.status);
  text("system-version", release.version);
  text("system-milestone", release.milestone);
  text("security-status", security.enabled ? "Enabled" : "Open mode");

  document.getElementById("health-list").innerHTML = Object.entries(health.engines)
    .map(([name, value]) => `<div class="row"><span>${name}</span>${badge(value)}</div>`)
    .join("");

  text("readiness-summary", readiness.ready ? "Ready" : "Needs attention");
  document.getElementById("readiness-list").innerHTML = readiness.checks
    .map((check) => `<div class="row"><span>${check.name}: ${check.message}</span>${badge(check.status)}</div>`)
    .join("");

  text("smoke-summary", smoke.ready ? "Pass" : "Needs attention");
  document.getElementById("smoke-list").innerHTML = smoke.checks
    .map((check) => `<div class="row"><span>${check.name}: ${check.message}</span>${badge(check.status)}</div>`)
    .join("");

  text("launch-summary", launch.ready ? "Ready" : "Needs attention");
  document.getElementById("launch-list").innerHTML = [
    ["Command", launch.command],
    ["Admin", launch.admin_url],
    ["Health", launch.api_url],
    ["Checks", launch.checks.map((check) => `${check.name}: ${check.status}`).join("; ")],
  ]
    .map(([name, value]) => `<div class="row"><span>${name}</span><strong>${value}</strong></div>`)
    .join("");

  text("manual-summary", manual.audience);
  document.getElementById("manual-list").innerHTML = manual.sections
    .map((section) => {
      const steps = section.steps.map((step) => `${step.title}: ${step.detail}`).join(" | ");
      return `<div class="row"><span>${section.title}</span><strong>${steps}</strong></div>`;
    })
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
    document.getElementById("smoke-list").innerHTML = "";
    document.getElementById("launch-list").innerHTML = "";
    document.getElementById("manual-list").innerHTML = "";
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

document.getElementById("local-bootstrap").addEventListener("click", () => {
  postJson(endpoints.localBootstrap)
    .then((bootstrap) => {
      text("launch-summary", bootstrap.ready ? "Workspace ready" : "Workspace warning");
      document.getElementById("launch-list").innerHTML = bootstrap.items
        .map((item) => {
          const status = item.created ? "created" : "present";
          return `<div class="row"><span>${item.name}</span><strong>${status}: ${item.path}</strong></div>`;
        })
        .join("");
    })
    .catch((error) => {
      text("launch-summary", "Error");
      document.getElementById("launch-list").innerHTML = `<div class="row"><span>Error</span><strong>${error.message}</strong></div>`;
    });
});

document.getElementById("release-package-create").addEventListener("click", () => {
  postJson(endpoints.releasePackage)
    .then((result) => {
      document.getElementById("release-package-path").value = result.archive_path;
      text("release-package-summary", "Created");
      setReleasePackageRows([
        ["Archive", result.archive_path],
        ["Version", result.manifest.version],
        ["Milestone", result.manifest.milestone],
        ["Files", result.manifest.total_files],
        ["Size", `${result.manifest.total_bytes} bytes`],
      ]);
    })
    .catch((error) => {
      text("release-package-summary", "Error");
      setReleasePackageRows([["Error", error.message]]);
    });
});

document.getElementById("release-package-inspect").addEventListener("click", () => {
  const archivePath = document.getElementById("release-package-path").value.trim();
  if (!archivePath) {
    text("release-package-summary", "Missing release package path");
    return;
  }
  getJson(`${endpoints.releasePackageInspect}?archive_path=${encodeURIComponent(archivePath)}`)
    .then((inspection) => {
      text("release-package-summary", inspection.ready ? "Package ready" : "Package warning");
      setReleasePackageRows([
        ["Archive", inspection.archive_path],
        ["Entries", inspection.entries.length],
        ["Warnings", inspection.warnings.length ? inspection.warnings.join("; ") : "None"],
      ]);
    })
    .catch((error) => {
      text("release-package-summary", "Error");
      setReleasePackageRows([["Error", error.message]]);
    });
});

document.getElementById("release-gate-run").addEventListener("click", () => {
  postJson(endpoints.releaseGate)
    .then((gate) => {
      document.getElementById("release-package-path").value = gate.package.archive_path;
      text("release-package-summary", gate.ready ? "Gate ready" : "Gate warning");
      setReleasePackageRows([
        ["Archive", gate.package.archive_path],
        ["Version", gate.release.version],
        ["Milestone", gate.release.milestone],
        ["Entries", gate.inspection.entries.length],
        ["Warnings", gate.warnings.length ? gate.warnings.join("; ") : "None"],
      ]);
    })
    .catch((error) => {
      text("release-package-summary", "Error");
      setReleasePackageRows([["Error", error.message]]);
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
  document.getElementById("smoke-list").innerHTML = "";
  document.getElementById("launch-list").innerHTML = "";
  document.getElementById("manual-list").innerHTML = "";
  refreshBackupManifest().catch(() => {
    text("backup-summary", "Error");
  });
});

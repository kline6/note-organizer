const { app, BrowserWindow } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const http = require("http");
const fs = require("fs");

let mainWindow = null;
let backendProc = null;
const PORT = 8000;

// Check if backend EXE exists, fall back to Python
function getBackendCmd() {
  const exePath = path.join(process.resourcesPath || "", "NoteOrganizer.exe");
  if (fs.existsSync(exePath)) return { cmd: exePath, args: [], cwd: path.dirname(exePath) };

  // Dev mode: use Python
  const python = findPython();
  const backendDir = path.join(__dirname, "..", "backend");
  return {
    cmd: python,
    args: ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(PORT), "--log-level", "warning"],
    cwd: backendDir,
  };
}

function findPython() {
  const bases = [
    process.env.LOCALAPPDATA + "/Programs/Python/Python312",
    process.env.LOCALAPPDATA + "/Programs/Python/Python313",
    "C:/Python312", "C:/Python313",
  ];
  for (const b of bases) {
    const exe = b + "/python.exe";
    if (fs.existsSync(exe)) return path.resolve(exe);
  }
  return "python";
}

function startBackend() {
  const { cmd, args, cwd } = getBackendCmd();
  console.log("Backend:", cmd, args.join(" "));
  console.log("cwd:", cwd);

  const env = Object.assign({}, process.env, {
    PYTHONUNBUFFERED: "1",
    NOTEORGANIZER_DATA_DIR: path.join(app.getPath("userData"), "data"),
  });

  backendProc = spawn(cmd, args, { cwd, env, stdio: ["ignore", "pipe", "pipe"] });
  backendProc.stdout.on("data", d => process.stdout.write("[BE] " + d));
  backendProc.stderr.on("data", d => process.stderr.write("[BE] " + d));
  backendProc.on("exit", code => { console.log("Backend exit:", code); backendProc = null; });
}

function waitForBackend(retries = 60) {
  return new Promise(resolve => {
    (function check(i) {
      if (i <= 0) return resolve(false);
      const req = http.get(`http://127.0.0.1:${PORT}/api/health`, () => resolve(true));
      req.on("error", () => setTimeout(() => check(i - 1), 500));
      req.setTimeout(1000, () => { req.destroy(); setTimeout(() => check(i - 1), 500); });
    })(retries);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400, height: 900, minWidth: 960, minHeight: 640,
    title: "NoteOrganizer",
    webPreferences: { nodeIntegration: false, contextIsolation: true },
    show: false,
  });
  mainWindow.setMenuBarVisibility(false);
  mainWindow.once("ready-to-show", () => mainWindow.show());
  mainWindow.loadURL(`http://127.0.0.1:${PORT}`);
  mainWindow.on("closed", () => { mainWindow = null; });
}

app.whenReady().then(async () => {
  startBackend();
  const ok = await waitForBackend();
  if (!ok) { console.error("Backend failed!"); app.quit(); return; }
  createWindow();
});

app.on("window-all-closed", () => {
  if (backendProc) { backendProc.kill(); backendProc = null; }
  app.quit();
});
app.on("before-quit", () => {
  if (backendProc) { backendProc.kill(); backendProc = null; }
});

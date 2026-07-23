#!/usr/bin/env node

"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const PACKAGE_ROOT = path.resolve(__dirname, "..");
const VENV_DIR = path.join(PACKAGE_ROOT, ".fantread-venv");
const MARKER_PATH = path.join(VENV_DIR, ".fantread-install.json");
const MINIMUM_PYTHON = Object.freeze([3, 11]);

function parsePythonVersion(value) {
  const match = String(value)
    .trim()
    .match(/^(\d+)\.(\d+)(?:\.\d+)?$/);
  if (!match) {
    return null;
  }
  return [Number(match[1]), Number(match[2])];
}

function isSupportedVersion(version) {
  if (!Array.isArray(version) || version.length < 2) {
    return false;
  }
  return (
    version[0] > MINIMUM_PYTHON[0] ||
    (version[0] === MINIMUM_PYTHON[0] && version[1] >= MINIMUM_PYTHON[1])
  );
}

function pythonCandidates(
  platform = process.platform,
  environment = process.env,
) {
  const candidates = [];
  if (environment.FANTREAD_PYTHON) {
    candidates.push({
      command: environment.FANTREAD_PYTHON,
      args: [],
      label: environment.FANTREAD_PYTHON,
    });
  }
  if (platform === "win32") {
    for (const version of ["3.13", "3.12", "3.11"]) {
      candidates.push({
        command: "py",
        args: [`-${version}`],
        label: `py -${version}`,
      });
    }
    candidates.push({ command: "python", args: [], label: "python" });
  } else {
    for (const command of [
      "python3.13",
      "python3.12",
      "python3.11",
      "python3",
      "python",
    ]) {
      candidates.push({ command, args: [], label: command });
    }
  }
  return candidates;
}

function inspectPython(candidate) {
  const probe = spawnSync(
    candidate.command,
    [
      ...candidate.args,
      "-c",
      "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')",
    ],
    {
      encoding: "utf8",
      windowsHide: true,
    },
  );
  if (probe.status !== 0) {
    return null;
  }
  const version = parsePythonVersion(probe.stdout);
  return isSupportedVersion(version) ? { ...candidate, version } : null;
}

function findPython() {
  for (const candidate of pythonCandidates()) {
    const result = inspectPython(candidate);
    if (result) {
      return result;
    }
  }
  throw new Error(
    "需要 Python 3.11 或更高版本。安装 Python 后重新运行 npm install -g fantread，" +
      "也可以通过 FANTREAD_PYTHON 指定解释器路径。",
  );
}

function venvPythonPath(platform = process.platform) {
  return platform === "win32"
    ? path.join(VENV_DIR, "Scripts", "python.exe")
    : path.join(VENV_DIR, "bin", "python");
}

function packageVersion() {
  return require(path.join(PACKAGE_ROOT, "package.json")).version;
}

function installationIsCurrent() {
  const python = venvPythonPath();
  if (!fs.existsSync(python) || !fs.existsSync(MARKER_PATH)) {
    return false;
  }
  try {
    const marker = JSON.parse(fs.readFileSync(MARKER_PATH, "utf8"));
    return marker.packageVersion === packageVersion();
  } catch {
    return false;
  }
}

function runChecked(command, args, label) {
  const result = spawnSync(command, args, {
    cwd: PACKAGE_ROOT,
    stdio: "inherit",
    windowsHide: true,
  });
  if (result.error) {
    throw new Error(`${label}失败：${result.error.message}`);
  }
  if (result.status !== 0) {
    throw new Error(`${label}失败，退出码 ${result.status ?? "未知"}`);
  }
}

function resetPrivateEnvironment() {
  if (
    path.dirname(VENV_DIR) !== PACKAGE_ROOT ||
    path.basename(VENV_DIR) !== ".fantread-venv"
  ) {
    throw new Error("内部环境路径异常，已停止安装");
  }
  fs.rmSync(VENV_DIR, { recursive: true, force: true });
}

function ensureInstalled(options = {}) {
  if (installationIsCurrent()) {
    return venvPythonPath();
  }

  const quiet = options.quiet === true;
  const python = findPython();
  resetPrivateEnvironment();
  if (!quiet) {
    console.error(
      `FanTread：正在使用 Python ${python.version.join(".")} 准备运行环境…`,
    );
  }
  runChecked(
    python.command,
    [...python.args, "-m", "venv", VENV_DIR],
    "创建 Python 环境",
  );
  runChecked(
    venvPythonPath(),
    [
      "-m",
      "pip",
      "install",
      "--quiet",
      "--disable-pip-version-check",
      "--no-input",
      PACKAGE_ROOT,
    ],
    "安装 FanTread Python 依赖",
  );
  fs.writeFileSync(
    MARKER_PATH,
    `${JSON.stringify(
      {
        packageVersion: packageVersion(),
        pythonVersion: python.version.join("."),
      },
      null,
      2,
    )}\n`,
    "utf8",
  );
  if (!quiet) {
    console.error("FanTread：运行环境准备完成，可直接使用 fan。");
  }
  return venvPythonPath();
}

if (require.main === module) {
  try {
    ensureInstalled();
  } catch (error) {
    console.error(`FanTread npm 安装失败：${error.message}`);
    process.exit(1);
  }
}

module.exports = {
  ensureInstalled,
  inspectPython,
  isSupportedVersion,
  parsePythonVersion,
  pythonCandidates,
  venvPythonPath,
};

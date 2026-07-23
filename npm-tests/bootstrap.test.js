"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const {
  isSupportedVersion,
  parsePythonVersion,
  pythonCandidates,
  venvPythonPath,
} = require("../scripts/bootstrap");

test("parses and validates supported Python versions", () => {
  assert.deepEqual(parsePythonVersion("3.11\n"), [3, 11]);
  assert.deepEqual(parsePythonVersion("3.13.4"), [3, 13]);
  assert.equal(parsePythonVersion("Python 3.13"), null);
  assert.equal(isSupportedVersion([3, 10]), false);
  assert.equal(isSupportedVersion([3, 11]), true);
  assert.equal(isSupportedVersion([4, 0]), true);
});

test("prefers an explicitly configured Python interpreter", () => {
  const candidates = pythonCandidates("linux", {
    FANTREAD_PYTHON: "/opt/python/bin/python",
  });
  assert.equal(candidates[0].command, "/opt/python/bin/python");
  assert.deepEqual(candidates[0].args, []);
});

test("uses the native virtual-environment layout", () => {
  assert.match(venvPythonPath("darwin"), /\.fantread-venv\/bin\/python$/);
  assert.match(
    venvPythonPath("win32"),
    /\.fantread-venv[\\/]Scripts[\\/]python\.exe$/,
  );
});

test("keeps npm and Python package versions synchronized", () => {
  const root = path.resolve(__dirname, "..");
  const packageVersion = require("../package.json").version;
  const pyproject = fs.readFileSync(path.join(root, "pyproject.toml"), "utf8");
  const match = pyproject.match(/^version = "([^"]+)"$/m);
  assert.ok(match);
  assert.equal(packageVersion, match[1]);
});

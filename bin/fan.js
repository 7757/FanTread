#!/usr/bin/env node

"use strict";

const { spawn } = require("node:child_process");
const { ensureInstalled } = require("../scripts/bootstrap");

let python;
try {
  python = ensureInstalled();
} catch (error) {
  console.error(`FanTread 启动失败：${error.message}`);
  process.exit(1);
}

const child = spawn(python, ["-m", "fantread", ...process.argv.slice(2)], {
  stdio: "inherit",
  env: process.env,
});

child.on("error", (error) => {
  console.error(`FanTread 启动失败：${error.message}`);
  process.exit(1);
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});

/**
 * Start only the Flask API, from the frontend directory.
 *
 * Uses the backend's virtualenv interpreter directly, so it does not matter
 * which python is on PATH or whether a venv is activated in this shell.
 */
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const backendDir = resolve(here, "..", "..", "backend");
const venvPython = process.platform === "win32"
  ? join(backendDir, "venv", "Scripts", "python.exe")
  : join(backendDir, "venv", "bin", "python");

if (!existsSync(venvPython)) {
  console.error(`\nNo virtualenv at:\n  ${venvPython}\n\nRun:\n  cd ../backend && python -m venv venv\n`);
  process.exit(1);
}

console.log("  API http://127.0.0.1:5000\n");
const child = spawn(venvPython, ["-u", "run.py"], { cwd: backendDir, stdio: "inherit" });
child.on("exit", (code) => process.exit(code ?? 0));

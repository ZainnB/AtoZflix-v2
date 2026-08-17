/**
 * Start the Flask API and the Vite dev server together, from this directory.
 *
 * Deliberately dependency-free (no `concurrently` / `npm-run-all`): it is ~60
 * lines of child_process, and adding a package to the frontend just to launch
 * the backend is not a trade worth making.
 *
 *   npm run dev:all     both servers
 *   npm run backend     API only
 *   npm run dev         frontend only
 *
 * Ctrl+C stops both. If either process dies, the other is torn down too, so you
 * never end up with an orphaned server holding port 5000 or 5173.
 */
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const backendDir = resolve(here, "..", "..", "backend");

// The venv interpreter, so the API runs against the project's pinned deps
// rather than whatever `python` happens to be first on PATH.
const venvPython = process.platform === "win32"
  ? join(backendDir, "venv", "Scripts", "python.exe")
  : join(backendDir, "venv", "bin", "python");

if (!existsSync(venvPython)) {
  console.error(
    `\nNo virtualenv found at:\n  ${venvPython}\n\n` +
    `Create it first:\n` +
    `  cd ../backend\n` +
    `  python -m venv venv\n` +
    `  venv\\Scripts\\python.exe -m pip install -r requirements.txt\n`
  );
  process.exit(1);
}

const children = [];
let shuttingDown = false;

/**
 * A server left over from a previous run holds the port, and the new process
 * then fails with an error that does not mention the real cause. Checking first
 * turns that into a one-line explanation.
 */
async function portInUse(port) {
  const { createConnection } = await import("node:net");
  return new Promise((resolve) => {
    const socket = createConnection({ port, host: "127.0.0.1" });
    const done = (result) => { socket.destroy(); resolve(result); };
    socket.setTimeout(700);
    socket.on("connect", () => done(true));
    socket.on("timeout", () => done(false));
    socket.on("error", () => done(false));
  });
}

const busy = [];
for (const [port, label] of [[5000, "API"], [5173, "Frontend"]]) {
  if (await portInUse(port)) busy.push(`  ${label} port ${port} is already in use`);
}
if (busy.length) {
  console.error(`\nCannot start - something is already running:\n${busy.join("\n")}\n`);
  console.error(
    process.platform === "win32"
      ? "Stop it with:\n  taskkill /F /IM python.exe /T\n  taskkill /F /IM node.exe /T\n"
      : "Find it with:  lsof -ti:5000,5173 | xargs kill\n"
  );
  process.exit(1);
}

function run(name, colour, command, args, cwd) {
  const child = spawn(command, args, { cwd, shell: false, stdio: ["ignore", "pipe", "pipe"] });
  const tag = `\x1b[${colour}m[${name}]\x1b[0m`;

  const pipe = (stream) => {
    let buffer = "";
    stream.on("data", (chunk) => {
      buffer += chunk.toString();
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) console.log(`${tag} ${line}`);
    });
  };
  pipe(child.stdout);
  pipe(child.stderr);

  child.on("exit", (code) => {
    console.log(`${tag} exited with code ${code}`);
    if (!shuttingDown) shutdown(code ?? 1);
  });

  children.push(child);
  return child;
}

function shutdown(code = 0) {
  if (shuttingDown) return;
  shuttingDown = true;
  for (const child of children) {
    if (child.exitCode === null) {
      // taskkill /T also takes the Werkzeug reloader's child process, which a
      // plain kill() on Windows would leave behind holding port 5000.
      if (process.platform === "win32") {
        spawn("taskkill", ["/pid", String(child.pid), "/f", "/t"], { stdio: "ignore" });
      } else {
        child.kill("SIGTERM");
      }
    }
  }
  setTimeout(() => process.exit(code), 400);
}

process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));

console.log("\n  API      http://127.0.0.1:5000");
console.log("  Frontend http://localhost:5173");
console.log("  Ctrl+C stops both.\n");

run("api", "36", venvPython, ["-u", "run.py"], backendDir);
run("web", "35", process.execPath, [join(here, "run-vite.mjs")], resolve(here, ".."));

/**
 * Launch Vite in-process.
 *
 * dev-all.mjs spawns this with process.execPath (the node binary) rather than
 * running `npm run dev` or `vite` directly, because on Windows those resolve to
 * .cmd shims that need shell:true - and a shell-wrapped child cannot be killed
 * cleanly, which leaves port 5173 held after Ctrl+C.
 */
import { createServer } from "vite";

// No options: Vite discovers vite.config.js from cwd on its own. Passing
// `configFile: true` is not the "auto-discover" flag - Vite expects a path
// there and throws on a boolean.
const server = await createServer();
await server.listen();
server.printUrls();

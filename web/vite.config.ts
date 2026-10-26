import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Phase 2 note: the `/api` proxy below is already wired, so the FastAPI adapter
// can be added later by running uvicorn on API_PROXY_TARGET. No frontend
// rewrite is required to switch from replay fixtures to live investigations.
const API_PROXY_TARGET = process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    // Required so the sandbox preview host (and any tunnelled origin) is served.
    allowedHosts: true,
    proxy: {
      "/api": {
        target: API_PROXY_TARGET,
        changeOrigin: true,
        // Server-sent events must not be buffered.
        configure: (proxy: { on: (event: string, cb: (res: { headers: Record<string, string> }) => void) => void }) => {
          proxy.on("proxyRes", (proxyRes) => {
            proxyRes.headers["cache-control"] = "no-cache";
          });
        },
      },
    },
  },
  preview: { host: "0.0.0.0", port: 4173, strictPort: true, allowedHosts: true },
  build: { outDir: "dist", sourcemap: false },
});

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { viteSingleFile } from "vite-plugin-singlefile";

/**
 * Standalone / offline build.
 *
 * Produces ONE self-contained HTML file (`standalone/rootcause-ai.html`) with the
 * JavaScript, CSS and self-hosted fonts all inlined. It needs no server, no
 * network and no sandbox — double-click it and the whole site runs, including
 * client-side routing (hash routing is used because file:// cannot pushState).
 *
 * This is an accessibility fallback for reviewing the design. The served build
 * (`npm run build`) remains the canonical artefact.
 */
export default defineConfig({
  plugins: [react(), tailwindcss(), viteSingleFile()],
  base: "./",
  define: {
    "import.meta.env.VITE_ROUTER": JSON.stringify("hash"),
  },
  build: {
    outDir: "standalone",
    emptyOutDir: true,
    // Inline the woff2 files as data URIs so nothing is fetched at runtime.
    assetsInlineLimit: 100 * 1024 * 1024,
    cssCodeSplit: false,
    sourcemap: false,
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
        manualChunks: undefined,
      },
    },
  },
});

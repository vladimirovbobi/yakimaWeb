import { defineConfig } from "vite";
import { resolve } from "path";

// Vite bundles Tailwind + Alpine + Motion + HTMX into static/dist/
// Whitenoise serves static/dist in dev; Cloudflare CDN in prod.

export default defineConfig({
  root: ".",
  base: "/static/",
  build: {
    outDir: "static/dist",
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, "static/src/js/main.js"),
        styles: resolve(__dirname, "static/src/css/tailwind.css"),
      },
      output: {
        entryFileNames: "js/[name].[hash].js",
        chunkFileNames: "js/[name].[hash].js",
        assetFileNames: ({ name }) => {
          if (/\.(css)$/.test(name ?? "")) return "css/[name].[hash][extname]";
          if (/\.(woff2?|ttf|otf|eot)$/.test(name ?? "")) return "fonts/[name][extname]";
          if (/\.(png|jpe?g|svg|gif|webp|avif)$/.test(name ?? "")) return "img/[name].[hash][extname]";
          return "assets/[name].[hash][extname]";
        },
      },
    },
    sourcemap: false,
    minify: "esbuild",
    target: "es2020",
  },
  server: { port: 5173 },
});

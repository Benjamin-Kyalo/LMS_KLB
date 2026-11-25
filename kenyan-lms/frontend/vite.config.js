import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The frontend runs on port 5173 and talks to the Django API on port 8000.
// A dev proxy lets us call "/api/..." directly without CORS surprises.
export default defineConfig({
  plugins: [
    react(),
  ],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/media": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.js",
    css: false,
  },
});

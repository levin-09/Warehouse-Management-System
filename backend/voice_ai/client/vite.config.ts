import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite proxies /api to the Pipecat runner on :7860 so the browser stays
// same-origin (required for getUserMedia). Point VITE_PIPECAT_WEBRTC_URL at a
// deployed server instead if you run the bot remotely.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:7860",
        changeOrigin: true,
      },
    },
  },
});

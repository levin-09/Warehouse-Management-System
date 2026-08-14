import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The backend API runs on :8000. During development we proxy /v1 and /api to
// it so the browser stays same-origin and avoids CORS entirely.
// The Pipecat voice bot runs on :7860; /api/offer (WebRTC SDP handshake) is
// proxied there too so the browser stays same-origin (getUserMedia requires it).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/v1": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/api": {
        target: "http://localhost:7860",
        changeOrigin: true,
      },
    },
  },
});

import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiTarget = env.VITE_DEV_API_PROXY_TARGET || "http://localhost:8000";

  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
          // Rewrite absolute Location headers (e.g. FastAPI's slash-normalising 307s)
          // so redirects stay same-origin and the session cookie survives.
          autoRewrite: true,
          cookieDomainRewrite: "",
        },
      },
    },
  };
});

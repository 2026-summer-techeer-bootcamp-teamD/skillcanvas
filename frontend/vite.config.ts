import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  // strictPort: 5173이 점유중이면 다른 포트로 도망가지 않고 에러 → 포트 일관성 유지
  // (로컬 실행기 CORS가 5173만 허용하므로 프론트도 5173 고정)
  server: { port: 5173, strictPort: true },
});

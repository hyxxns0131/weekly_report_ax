// KHS. 화면은 정적 파일로만 만든다(output: "export"). 서버 기능(API Routes, Server Actions, SSR, middleware) 금지.
// 이유: 마지막에 exe로 묶을 때 화면은 정적 파일이어야 한다 (AGENTS.md 0-2).
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;

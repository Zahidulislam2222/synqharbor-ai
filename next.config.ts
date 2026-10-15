import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  poweredByHeader: false,
  // Use the documented compiler API route; CLI output capture fails in this WSL build.
  experimental: { useTypeScriptCli: false },
};

export default nextConfig;

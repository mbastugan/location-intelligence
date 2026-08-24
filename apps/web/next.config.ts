import type { NextConfig } from "next";

const isStatic = process.env.NEXT_PUBLIC_DATA_MODE === "static";
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const nextConfig: NextConfig = {
  output: isStatic ? "export" : undefined,
  images: { unoptimized: isStatic },
  trailingSlash: isStatic,
  basePath: basePath || undefined,
  assetPrefix: basePath || undefined,
};

export default nextConfig;

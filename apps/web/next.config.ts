import type { NextConfig } from "next";

const isStatic = process.env.NEXT_PUBLIC_DATA_MODE === "static";

const nextConfig: NextConfig = {
  output: isStatic ? "export" : undefined,
  images: { unoptimized: isStatic },
  trailingSlash: isStatic,
};

export default nextConfig;

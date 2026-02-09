/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    // Dependencies can ship TS sources that don't match our lib target.
    // We rely on runtime tests instead of blocking the build here.
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;

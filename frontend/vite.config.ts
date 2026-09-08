import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // Bind both IPv4 and IPv6 loopback — depending on the machine, browsers
    // may resolve "*.localhost" hostnames to either 127.0.0.1 or ::1.
    host: true,
    // Accept requests addressed to rsemarketreports.localhost (and any other
    // *.localhost host) — browsers resolve any ".localhost" hostname to the
    // loopback address natively, so this needs no hosts-file entry, but
    // Vite's dev-server host-header check must be told to allow it.
    allowedHosts: ['.localhost'],
  },
})

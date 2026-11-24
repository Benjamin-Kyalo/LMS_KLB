import type { CapacitorConfig } from "@capacitor/cli";

// The PWA build in `dist/` is the single web app shared by browsers and the
// native wrapper. No native project-specific secrets or signing material live
// here. Environment variables are optional and intended for local development
// only; production builds use the packaged app shell and an HTTPS API.
const serverUrl = process.env.CAPACITOR_SERVER_URL;
const cleartext = process.env.CAPACITOR_CLEARTEXT === "true";

const config: CapacitorConfig = {
  appId: "org.klb.learning",
  appName: "KLB Learning",
  webDir: "dist",
  ...(serverUrl
    ? {
        server: {
          url: serverUrl,
          // Only allow plain HTTP for an explicitly configured local dev server.
          cleartext: cleartext,
        },
      }
    : {}),
};

export default config;

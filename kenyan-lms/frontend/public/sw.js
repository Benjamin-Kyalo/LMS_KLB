/* One-release kill switch for the retired PWA service worker.
 * This file is intentionally never registered. Browsers that still hold the
 * old registration will fetch it on update, activate it, drop cached assets
 * and unregister themselves. Remove this file after the rollout. */
self.addEventListener("install", (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(keys.map((key) => caches.delete(key)));
      await self.registration.unregister();
      const windows = await self.clients.matchAll({
        type: "window",
        includeUncontrolled: true,
      });
      windows.forEach((client) => client.navigate(client.url));
    })(),
  );
});

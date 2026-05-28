self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('servsolda-v6').then((cache) => cache.addAll([
      '/',
      '/static/pwa-icon.png?v=5',
      '/static/manifest_servsolda.json?v=5'
    ])).then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(keyList.map((key) => {
        if (key !== 'servsolda-v6') {
          return caches.delete(key);
        }
      }));
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => response || fetch(e.request)),
  );
});

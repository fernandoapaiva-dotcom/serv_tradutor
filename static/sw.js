self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('servsolda-v8').then((cache) => cache.addAll([
      '/',
      '/static/pwa-icon.png?v=6',
      '/static/manifest_servsolda.json?v=6'
    ])).then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(keyList.map((key) => {
        if (key !== 'servsolda-v8') {
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

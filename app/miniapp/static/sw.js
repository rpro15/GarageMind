/**
 * Service Worker для GarageMind AI (PWA)
 * 
 * Установка: при открытии сайта Safari предложит установить на экран «Домой»
 * Офлайн-режим: кэширует index.html, CSS, JS, языковые файлы
 */

const CACHE_NAME = 'garagemind-v2';
const urlsToCache = [
  '/miniapp/index.html',
  '/miniapp/static/style.css',
  '/miniapp/static/scripts.js',
  '/miniapp/static/manifest.json',
  '/miniapp/static/lang/ru.json',
  '/miniapp/static/lang/en.json',
  '/miniapp/static/lang/kk.json',
  '/miniapp/static/lang/uz.json',
  '/miniapp/static/lang/ky.json',
  '/miniapp/static/lang/tg.json',
  '/miniapp/static/lang/hy.json',
  '/miniapp/static/lang/ka.json',
];

// Установка — кэшируем основные файлы
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Кэширование базовых файлов');
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

// Активация — удаляем старые кэши
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Удаление старого кэша:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Стратегия: Cache First (сначала кэш, потом сеть)
self.addEventListener('fetch', event => {
  // Не кэшируем API запросы
  if (event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        if (cachedResponse) {
          // Есть в кэше — отдаём
          return cachedResponse;
        }

        // Нет в кэше — идём в сеть
        return fetch(event.request)
          .then(response => {
            // Кэшируем только статику
            if (
              response.status === 200 &&
              event.request.url.startsWith(self.location.origin) &&
              (
                event.request.url.includes('/miniapp/') ||
                event.request.url.includes('/lang/')
              )
            ) {
              const responseClone = response.clone();
              caches.open(CACHE_NAME).then(cache => {
                cache.put(event.request, responseClone);
              });
            }
            return response;
          })
          .catch(() => {
            // Офлайн — показываем заглушку
            if (event.request.mode === 'navigate') {
              return caches.match('/miniapp/index.html');
            }
          });
      })
  );
});

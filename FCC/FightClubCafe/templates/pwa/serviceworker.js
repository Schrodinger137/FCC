self.addEventListener("fetch", function(event) {
    event.respondWith(
        caches.match(event.request).then(function(response) {

            // Si ya está en cache → úsalo
            if (response) return response;

            // Si no → lo descargo y lo guardo
            return fetch(event.request).then(function(networkResponse) {

                // Cachea solo si es imagen
                if (event.request.url.match(/\.(png|jpg|jpeg|gif|webp|svg)$/)) {
                    return caches.open("dynamic-images").then(function(cache) {
                        cache.put(event.request, networkResponse.clone());
                        return networkResponse;
                    });
                }

                return networkResponse;
            });
        })
    );
});

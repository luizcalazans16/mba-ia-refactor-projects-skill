// Cache em memória com limite de entradas (evita crescimento ilimitado). Instanciado e injetado pelo composition root.
class InMemoryCache {
    constructor({ maxEntries = 1000 } = {}) {
        this.maxEntries = maxEntries;
        this.store = new Map();
    }

    set(key, value) {
        this.store.delete(key);
        this.store.set(key, value);
        if (this.store.size > this.maxEntries) {
            this.store.delete(this.store.keys().next().value);
        }
    }

    get(key) {
        return this.store.get(key);
    }
}

module.exports = InMemoryCache;

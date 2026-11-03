// Logger mínimo com níveis (sem dependências). Troque por pino/winston se precisar de JSON estruturado.
const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

function createLogger(level = 'info') {
    const threshold = LEVELS[level] ?? LEVELS.info;
    const write = (name, method) => (...args) => {
        if (LEVELS[name] >= threshold) console[method](`[${new Date().toISOString()}] ${name.toUpperCase()}`, ...args);
    };
    return {
        debug: write('debug', 'debug'),
        info: write('info', 'info'),
        warn: write('warn', 'warn'),
        error: write('error', 'error'),
    };
}

module.exports = createLogger;

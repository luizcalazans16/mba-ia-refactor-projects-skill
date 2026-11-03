const crypto = require('node:crypto');
const { ForbiddenError } = require('../errors');

// Protege rotas administrativas: exige o cabeçalho X-Admin-Token igual a ADMIN_TOKEN.
// Sem ADMIN_TOKEN configurado, as rotas ficam desabilitadas.
function requireAdminToken(expectedToken) {
    const expected = Buffer.from(expectedToken || '');
    return (req, res, next) => {
        const given = Buffer.from(req.get('X-Admin-Token') || '');
        const ok = expected.length > 0 && given.length === expected.length && crypto.timingSafeEqual(given, expected);
        return ok ? next() : next(new ForbiddenError());
    };
}

module.exports = requireAdminToken;

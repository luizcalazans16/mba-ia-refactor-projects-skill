const crypto = require('node:crypto');

const KEY_LENGTH = 64;
const SALT_BYTES = 16;

// Hash de senha com scrypt + salt aleatório (formato: scrypt$<salt>$<hash>).
const passwordHasher = {
    hash(password) {
        const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
        const hash = crypto.scryptSync(password, salt, KEY_LENGTH).toString('hex');
        return `scrypt$${salt}$${hash}`;
    },

    verify(password, stored) {
        const [scheme, salt, hash] = String(stored || '').split('$');
        if (scheme !== 'scrypt' || !salt || !hash) return false;
        const expected = Buffer.from(hash, 'hex');
        const actual = crypto.scryptSync(password, salt, expected.length);
        return crypto.timingSafeEqual(expected, actual);
    },

    // Para contas criadas sem senha: valor aleatório, impossível de adivinhar.
    unusable() {
        return passwordHasher.hash(crypto.randomBytes(32).toString('hex'));
    },
};

module.exports = passwordHasher;

// Configuração central: tudo que varia por ambiente vem de variáveis de ambiente.
// Segredos não têm valor padrão no código.
module.exports = Object.freeze({
    port: Number(process.env.PORT) || 3000,
    dbPath: process.env.DB_PATH || ':memory:',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    // Vazio = endpoints /api/admin/* desabilitados (respondem 403).
    adminToken: process.env.ADMIN_TOKEN || '',
    logLevel: process.env.LOG_LEVEL || 'info',
});

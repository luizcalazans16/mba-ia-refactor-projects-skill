// Entry point (`npm start`): carrega a configuração, monta a aplicação e sobe o servidor HTTP.
const config = require('./config');
const createApp = require('./createApp');

createApp(config)
    .then(({ app, logger }) => {
        app.listen(config.port, () => logger.info(`LMS API rodando na porta ${config.port}`));
    })
    .catch((err) => {
        console.error('Falha ao iniciar a aplicação', err);
        process.exit(1);
    });

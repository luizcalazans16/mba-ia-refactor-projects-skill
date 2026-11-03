// Composition root: abre o banco, instancia models/services/controllers e monta a aplicação Express.
const express = require('express');

const Database = require('./database/connection');
const { createSchema, seed } = require('./database/schema');
const UserModel = require('./models/UserModel');
const CourseModel = require('./models/CourseModel');
const EnrollmentModel = require('./models/EnrollmentModel');
const { PaymentModel } = require('./models/PaymentModel');
const AuditLogModel = require('./models/AuditLogModel');
const passwordHasher = require('./services/passwordHasher');
const FakePaymentGateway = require('./services/paymentGateway');
const InMemoryCache = require('./services/cache');
const createLogger = require('./services/logger');
const { CheckoutController } = require('./controllers/CheckoutController');
const ReportController = require('./controllers/ReportController');
const UserController = require('./controllers/UserController');
const createRoutes = require('./routes');
const createErrorHandler = require('./middlewares/errorHandler');

async function createApp(config) {
    const logger = createLogger(config.logLevel);

    const db = await Database.open(config.dbPath);
    await createSchema(db);
    await seed(db, { passwordHasher });

    const models = {
        userModel: new UserModel(db),
        courseModel: new CourseModel(db),
        enrollmentModel: new EnrollmentModel(db),
        paymentModel: new PaymentModel(db),
        auditLogModel: new AuditLogModel(db),
    };

    const checkoutController = new CheckoutController({
        db,
        ...models,
        paymentGateway: new FakePaymentGateway({ apiKey: config.paymentGatewayKey, logger }),
        passwordHasher,
        cache: new InMemoryCache(),
    });
    const reportController = new ReportController(models);
    const userController = new UserController({ db, ...models });

    const app = express();
    app.use(express.json());
    app.use(createRoutes({ checkoutController, reportController, userController, adminToken: config.adminToken }));
    app.use(createErrorHandler(logger));

    return { app, db, logger };
}

module.exports = createApp;

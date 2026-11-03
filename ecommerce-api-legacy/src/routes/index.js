// Camada View: mapeia rotas HTTP para controllers e serializa as respostas.
const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const requireAdminToken = require('../middlewares/requireAdminToken');

function createRoutes({ checkoutController, reportController, userController, adminToken }) {
    const router = express.Router();

    router.post('/api/checkout', asyncHandler(async (req, res) => {
        res.status(200).json(await checkoutController.checkout(req.body));
    }));

    router.get('/api/admin/financial-report', requireAdminToken(adminToken), asyncHandler(async (req, res) => {
        res.json(await reportController.financialReport());
    }));

    router.delete('/api/users/:id', asyncHandler(async (req, res) => {
        res.send(await userController.deleteUser(req.params.id));
    }));

    return router;
}

module.exports = createRoutes;

const { PAYMENT_STATUS } = require('../models/PaymentModel');

// Gateway simulado: aprova cartões cuja bandeira começa com o dígito configurado (4 = Visa no ambiente de testes).
const APPROVED_CARD_PREFIX = '4';

class FakePaymentGateway {
    constructor({ apiKey, logger }) {
        this.apiKey = apiKey;
        this.logger = logger;
    }

    charge({ cardNumber, amount }) {
        this.logger.info(`Processando pagamento de ${amount} no cartão final ${cardNumber.slice(-4)}`);
        return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
    }
}

module.exports = FakePaymentGateway;

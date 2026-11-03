const { ValidationError, NotFoundError } = require('../errors');
const { PAYMENT_STATUS } = require('../models/PaymentModel');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CARD_PATTERN = /^\d{4,19}$/;

const isNonEmptyString = (value) => typeof value === 'string' && value.trim() !== '';

// Converte o contrato público (usr, eml, pwd, c_id, card) em nomes internos e valida tipos/formatos.
function parseCheckoutRequest(body = {}) {
    const { usr: name, eml: email, pwd: password, c_id: rawCourseId, card: cardNumber } = body || {};
    if (!name || !email || !rawCourseId || !cardNumber) throw new ValidationError('Bad Request');

    const courseId = Number(rawCourseId);
    const valid = isNonEmptyString(name)
        && isNonEmptyString(email) && EMAIL_PATTERN.test(email)
        && Number.isInteger(courseId) && courseId > 0
        && typeof cardNumber === 'string' && CARD_PATTERN.test(cardNumber)
        && (password === undefined || password === null || typeof password === 'string');
    if (!valid) throw new ValidationError('Bad Request');

    return { name: name.trim(), email: email.trim(), password, courseId, cardNumber };
}

class CheckoutController {
    constructor({ db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentGateway, passwordHasher, cache }) {
        Object.assign(this, { db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentGateway, passwordHasher, cache });
    }

    async checkout(body) {
        const { name, email, password, courseId, cardNumber } = parseCheckoutRequest(body);

        const course = await this.courseModel.findActiveById(courseId);
        if (!course) throw new NotFoundError('Curso não encontrado');

        const paymentStatus = this.paymentGateway.charge({ cardNumber, amount: course.price });
        if (paymentStatus === PAYMENT_STATUS.DENIED) throw new ValidationError('Pagamento recusado');

        const { userId, enrollmentId } = await this.db.transaction(async () => {
            const existing = await this.userModel.findByEmail(email);
            const id = existing ? existing.id : await this.userModel.create({
                name,
                email,
                passwordHash: password ? this.passwordHasher.hash(password) : this.passwordHasher.unusable(),
            });
            const newEnrollmentId = await this.enrollmentModel.create(id, course.id);
            await this.paymentModel.create(newEnrollmentId, course.price, paymentStatus);
            await this.auditLogModel.record(`Checkout curso ${course.id} por ${id}`);
            return { userId: id, enrollmentId: newEnrollmentId };
        });

        this.cache.set(`last_checkout_${userId}`, course.title);
        return { msg: 'Sucesso', enrollment_id: enrollmentId };
    }
}

module.exports = { CheckoutController, parseCheckoutRequest };

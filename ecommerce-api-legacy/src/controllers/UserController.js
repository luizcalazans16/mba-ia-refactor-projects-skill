const { NotFoundError, ValidationError } = require('../errors');

class UserController {
    constructor({ db, userModel, enrollmentModel, paymentModel }) {
        Object.assign(this, { db, userModel, enrollmentModel, paymentModel });
    }

    // Remove o usuário junto com matrículas e pagamentos, numa única transação (sem registros órfãos).
    async deleteUser(rawId) {
        const id = Number(rawId);
        if (!Number.isInteger(id) || id <= 0) throw new ValidationError('Bad Request');

        await this.db.transaction(async () => {
            const user = await this.userModel.findById(id);
            if (!user) throw new NotFoundError('Usuário não encontrado');
            await this.paymentModel.deleteByUser(id);
            await this.enrollmentModel.deleteByUser(id);
            await this.userModel.delete(id);
        });
        return 'Usuário deletado';
    }
}

module.exports = UserController;

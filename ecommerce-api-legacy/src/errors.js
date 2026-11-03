// Erros de domínio: controllers lançam, o middleware de erro converte em resposta HTTP.
class AppError extends Error {
    constructor(message, status = 500) {
        super(message);
        this.name = this.constructor.name;
        this.status = status;
    }
}

class ValidationError extends AppError {
    constructor(message = 'Bad Request') { super(message, 400); }
}

class ForbiddenError extends AppError {
    constructor(message = 'Acesso negado') { super(message, 403); }
}

class NotFoundError extends AppError {
    constructor(message) { super(message, 404); }
}

module.exports = { AppError, ValidationError, ForbiddenError, NotFoundError };

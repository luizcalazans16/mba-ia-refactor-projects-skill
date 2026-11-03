const sqlite3 = require('sqlite3');

// Wrapper do driver sqlite3 com Promises e transações serializadas.
class Database {
    constructor(connection) {
        this.connection = connection;
        this.transactionQueue = Promise.resolve();
    }

    static open(path) {
        return new Promise((resolve, reject) => {
            const connection = new sqlite3.Database(path, (err) => (err ? reject(err) : resolve(new Database(connection))));
        });
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.run(sql, params, function onRun(err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    // Executa `work` dentro de BEGIN/COMMIT, com ROLLBACK em erro.
    // As transações são enfileiradas porque a conexão SQLite é única.
    transaction(work) {
        const execute = async () => {
            await this.run('BEGIN');
            try {
                const result = await work();
                await this.run('COMMIT');
                return result;
            } catch (err) {
                await this.run('ROLLBACK');
                throw err;
            }
        };
        const result = this.transactionQueue.then(execute, execute);
        this.transactionQueue = result.catch(() => {});
        return result;
    }

    close() {
        return new Promise((resolve, reject) => this.connection.close((err) => (err ? reject(err) : resolve())));
    }
}

module.exports = Database;

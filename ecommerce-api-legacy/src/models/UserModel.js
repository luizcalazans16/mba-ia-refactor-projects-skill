class UserModel {
    constructor(db) { this.db = db; }

    findByEmail(email) {
        return this.db.get('SELECT id, name, email FROM users WHERE email = ?', [email]);
    }

    findById(id) {
        return this.db.get('SELECT id, name, email FROM users WHERE id = ?', [id]);
    }

    async create({ name, email, passwordHash }) {
        const { lastID } = await this.db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
        return lastID;
    }

    delete(id) {
        return this.db.run('DELETE FROM users WHERE id = ?', [id]);
    }
}

module.exports = UserModel;

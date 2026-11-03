const { PAYMENT_STATUS } = require('../models/PaymentModel');

class ReportController {
    constructor({ courseModel }) {
        this.courseModel = courseModel;
    }

    // Faturamento por curso (somente pagamentos PAID) e lista de alunos com o valor pago.
    async financialReport() {
        const rows = await this.courseModel.findAllWithEnrollments();
        const byCourse = new Map();

        for (const row of rows) {
            if (!byCourse.has(row.course_id)) {
                byCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
            }
            if (row.enrollment_id === null) continue;

            const entry = byCourse.get(row.course_id);
            if (row.payment_status === PAYMENT_STATUS.PAID) entry.revenue += row.payment_amount;
            entry.students.push({ student: row.student_name ?? 'Unknown', paid: row.payment_amount ?? 0 });
        }

        return [...byCourse.values()];
    }
}

module.exports = ReportController;

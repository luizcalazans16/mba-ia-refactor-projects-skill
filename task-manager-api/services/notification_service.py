"""Notificações por e-mail. Credenciais vêm da configuração; sem SMTP_HOST as mensagens só vão para o log."""
import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, host="", port=587, user="", password="", timeout=10):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.timeout = timeout

    @property
    def enabled(self):
        return bool(self.host)

    def send_email(self, to, subject, body):
        if not self.enabled:
            logger.info("E-mail (SMTP desabilitado) para %s: %s", to, subject)
            return False
        message = EmailMessage()
        message["From"], message["To"], message["Subject"] = self.user, to, subject
        message.set_content(body)
        try:
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as server:
                server.starttls()
                if self.user:
                    server.login(self.user, self.password)
                server.send_message(message)
            logger.info("E-mail enviado para %s", to)
            return True
        except (smtplib.SMTPException, OSError):
            logger.exception("Falha ao enviar e-mail para %s", to)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
                f"Prioridade: {task.priority}\nStatus: {task.status}")
        return self.send_email(user.email, subject, body)

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        return self.send_email(user.email, subject, body)

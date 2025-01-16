from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib

from src.core.exceptions import BadRequestException


class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = 'info@atlantys.kz'
        self.smtp_password = 'pnvcpqruwppqvnhw '
        self.sender_email ='info@atlantys.kz'
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    async def send_email(self, to_email: str, subject: str, html_content: str):
        print(self.smtp_username,self.smtp_password)
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender_email
        message["To"] = to_email
        
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
        except Exception as e:
            raise BadRequestException(f"Failed to send email: {str(e)}")
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..utils.logger import logger

class EmailService:
    def __init__(self, smtp_host, smtp_port, username, auth_code):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.auth_code = auth_code

    def send_email(self, recipient, subject, body):
        try:
            # Log email attempt
            logger.log_email_attempt(recipient, subject)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            logger.log_smtp_connection(self.smtp_host, self.smtp_port)
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            
            # Authenticate
            logger.log_smtp_auth(self.username)
            server.login(self.username, self.auth_code)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            # Log success
            logger.log_email_success(recipient)
            return True
            
        except Exception as e:
            # Log failure
            logger.log_email_failure(recipient, str(e))
            return False
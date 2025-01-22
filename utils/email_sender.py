"""
Email sender utility with robust error handling and retries
"""
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self, config):
        self.smtp_server = config['SMTP_SERVER']
        self.smtp_port = config['SMTP_PORT']
        self.sender_email = str(config['SENDER_EMAIL'])
        self.sender_password = str(config['SENDER_PASSWORD'])
        self.ssl_context = ssl.create_default_context()
        
        # Configure SSL context with more lenient settings
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
    def _create_message(self, to_email, content):
        """Create email message with both HTML and plain text versions"""
        msg = MIMEMultipart('alternative')
        msg['From'] = self.sender_email
        msg['To'] = to_email
        msg['Subject'] = f"Daily Brief - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Create plain text version
        text_content = self._strip_html(content) if '<' in content else content
        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        
        # Create HTML version
        html_content = content if '<' in content else content.replace('\n', '<br>')
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        return msg
        
    def _strip_html(self, html_content):
        """Remove HTML tags for plain text version"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html_content)
        
    def _encode_base64(self, s):
        """Encode string to base64"""
        return base64.b64encode(s.encode('utf-8')).decode('utf-8')
        
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=4, max=10))
    def send_email(self, to_email, content):
        """Send email with retries and proper error handling"""
        try:
            logger.info(f"Attempting to send email to {to_email}")
            
            with smtplib.SMTP_SSL(self.smtp_server, 
                                self.smtp_port,
                                context=self.ssl_context,
                                timeout=30) as server:
                
                # Enable debug output
                server.set_debuglevel(1)
                
                # Initialize connection
                server.ehlo_or_helo_if_needed()
                
                # Prepare authentication
                auth_string = f"\000{self.sender_email}\000{self.sender_password}"
                auth_base64 = self._encode_base64(auth_string)
                
                try:
                    server.docmd("AUTH", f"PLAIN {auth_base64}")
                except smtplib.SMTPResponseException as e:
                    if e.smtp_code == 334:
                        server.docmd(auth_base64)
                
                logger.info("SMTP authentication successful")
                
                # Create and send message
                msg = self._create_message(to_email, content)
                server.send_message(msg)
                logger.info(f"Email sent successfully to {to_email}")
                
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {e}")
            logger.error(f"Server response code: {e.smtp_code}")
            logger.error(f"Server response: {e.smtp_error}")
            raise
            
        except smtplib.SMTPResponseException as e:
            logger.error(f"SMTP Response error: Code {e.smtp_code}")
            logger.error(f"SMTP Response message: {e.smtp_error}")
            raise
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error occurred: {e}")
            raise
            
        except ssl.SSLError as e:
            logger.error(f"SSL error occurred: {e}")
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
            
class EmailManager:
    def __init__(self, email_config, subscribers):
        self.email_sender = EmailSender(email_config)
        self.subscribers = subscribers
        
    async def send_daily_brief(self, content):
        """Send daily brief to all subscribers"""
        success_count = 0
        failure_count = 0
        results = []
        
        for subscriber in self.subscribers:
            try:
                self.email_sender.send_email(subscriber, content)
                success_count += 1
                results.append({
                    'email': subscriber,
                    'status': 'success'
                })
                logger.info(f"Successfully sent email to {subscriber}")
                
            except Exception as e:
                failure_count += 1
                results.append({
                    'email': subscriber,
                    'status': 'failed',
                    'error': str(e)
                })
                logger.error(f"Failed to send email to {subscriber}: {e}")
                continue
                
        return {
            'success': success_count,
            'failure': failure_count,
            'total': len(self.subscribers),
            'details': results
        }
import logging
from datetime import datetime
import os

class DailyBriefLogger:
    def __init__(self):
        self.logger = logging.getLogger('daily_brief_bot')
        self.logger.setLevel(logging.DEBUG)
        
        # Create logs directory if it doesn't exist
        self.logs_dir = 'logs'
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # File handler for all logs
        log_file = os.path.join(self.logs_dir, f'daily_brief_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Create error logs file
        error_file = os.path.join(self.logs_dir, f'error_{datetime.now().strftime("%Y%m%d")}.log')
        error_handler = logging.FileHandler(error_file)
        error_handler.setLevel(logging.ERROR)
        
        # Create formatters and add them to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
    
    def log_email_attempt(self, recipient, subject):
        """Log email sending attempt"""
        self.logger.info(f'Attempting to send email - Recipient: {recipient}, Subject: {subject}')
    
    def log_smtp_connection(self, host, port):
        """Log SMTP connection attempt"""
        self.logger.info(f'Establishing SMTP connection - Host: {host}, Port: {port}')
    
    def log_smtp_auth(self, username):
        """Log SMTP authentication attempt"""
        self.logger.info(f'Authenticating SMTP - Username: {username}')
    
    def log_email_success(self, recipient):
        """Log successful email delivery"""
        self.logger.info(f'Email successfully sent to {recipient}')
    
    def log_email_failure(self, recipient, error):
        """Log email sending failure"""
        self.logger.error(f'Failed to send email to {recipient} - Error: {str(error)}')
    
    def log_api_request(self, endpoint, method):
        """Log API request"""
        self.logger.info(f'API Request - Endpoint: {endpoint}, Method: {method}')
    
    def log_api_response(self, endpoint, status_code):
        """Log API response"""
        self.logger.info(f'API Response - Endpoint: {endpoint}, Status: {status_code}')
    
    def log_api_error(self, endpoint, error):
        """Log API error"""
        self.logger.error(f'API Error - Endpoint: {endpoint}, Error: {str(error)}')

# Create singleton instance
logger = DailyBriefLogger()
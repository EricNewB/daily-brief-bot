import unittest
import os
import shutil
from datetime import datetime
from src.utils.logger import DailyBriefLogger

class TestLogger(unittest.TestCase):
    def setUp(self):
        # Create test logs directory
        self.test_logs_dir = 'test_logs'
        if os.path.exists(self.test_logs_dir):
            shutil.rmtree(self.test_logs_dir)
        os.makedirs(self.test_logs_dir)
        
        # Initialize logger
        self.logger = DailyBriefLogger()
        self.logger.logs_dir = self.test_logs_dir
    
    def tearDown(self):
        # Clean up test logs
        if os.path.exists(self.test_logs_dir):
            shutil.rmtree(self.test_logs_dir)
    
    def test_log_file_creation(self):
        """Test if log files are created"""
        self.logger.log_email_attempt('test@example.com', 'Test Subject')
        
        # Check if log files exist
        date_str = datetime.now().strftime('%Y%m%d')
        self.assertTrue(os.path.exists(f'{self.test_logs_dir}/daily_brief_{date_str}.log'))
        self.assertTrue(os.path.exists(f'{self.test_logs_dir}/error_{date_str}.log'))
    
    def test_log_email_process(self):
        """Test email process logging"""
        self.logger.log_email_attempt('test@example.com', 'Test Subject')
        self.logger.log_smtp_connection('smtp.test.com', 587)
        self.logger.log_smtp_auth('test_user')
        self.logger.log_email_success('test@example.com')
        
        # Read log file
        date_str = datetime.now().strftime('%Y%m%d')
        with open(f'{self.test_logs_dir}/daily_brief_{date_str}.log', 'r') as f:
            log_content = f.read()
            
        # Check if all log messages are present
        self.assertIn('Attempting to send email', log_content)
        self.assertIn('Establishing SMTP connection', log_content)
        self.assertIn('Authenticating SMTP', log_content)
        self.assertIn('Email successfully sent', log_content)
    
    def test_error_logging(self):
        """Test error logging"""
        test_error = "Connection timeout"
        self.logger.log_email_failure('test@example.com', test_error)
        
        # Check error log
        date_str = datetime.now().strftime('%Y%m%d')
        with open(f'{self.test_logs_dir}/error_{date_str}.log', 'r') as f:
            error_content = f.read()
        
        self.assertIn(test_error, error_content)

if __name__ == '__main__':
    unittest.main()
import unittest
from unittest.mock import patch, MagicMock
from src.services.email_service import EmailService

class TestEmailService(unittest.TestCase):
    def setUp(self):
        self.email_service = EmailService(
            smtp_host='smtp.test.com',
            smtp_port=587,
            username='test@example.com',
            auth_code='test_auth_code'
        )
    
    @patch('smtplib.SMTP')
    def test_successful_email_send(self, mock_smtp):
        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        # Test sending email
        result = self.email_service.send_email(
            recipient='recipient@example.com',
            subject='Test Subject',
            body='Test Body'
        )
        
        # Verify SMTP interactions
        self.assertTrue(result)
        mock_smtp.assert_called_once_with('smtp.test.com', 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('test@example.com', 'test_auth_code')
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_failed_email_send(self, mock_smtp):
        # Setup mock to raise exception
        mock_smtp.side_effect = Exception('Test error')
        
        # Test sending email
        result = self.email_service.send_email(
            recipient='recipient@example.com',
            subject='Test Subject',
            body='Test Body'
        )
        
        # Verify failure handling
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
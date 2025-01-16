from src.services.email_service import EmailService
from test_config import EMAIL_CONFIG, TEST_EMAIL

def test_email_sending():
    # Initialize email service with test config
    email_service = EmailService(
        smtp_host=EMAIL_CONFIG['smtp_host'],
        smtp_port=EMAIL_CONFIG['smtp_port'],
        username=EMAIL_CONFIG['username'],
        auth_code=EMAIL_CONFIG['auth_code']
    )
    
    # Send test email
    result = email_service.send_email(
        recipient=TEST_EMAIL['recipient'],
        subject=TEST_EMAIL['subject'],
        body=TEST_EMAIL['body']
    )
    
    if result:
        print('✅ Test email sent successfully!')
        print('Please check the following:')
        print('1. Test email received at:', TEST_EMAIL['recipient'])
        print('2. Log files in the logs directory')
    else:
        print('❌ Failed to send test email')
        print('Please check the error logs in the logs directory')

if __name__ == '__main__':
    test_email_sending()
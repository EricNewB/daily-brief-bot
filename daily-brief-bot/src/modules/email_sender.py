import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailSender:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.smtp_server = 'smtp.yeah.net'
        self.smtp_port = 465
    
    def create_html_digest(self, news_items):
        """Create HTML formatted digest from news items"""
        html = ['<html><body>']
        
        for item in news_items:
            html.append(f'''
            <div style="margin-bottom: 20px;">
                <h2><a href="{item['url']}">{item['title']}</a></h2>
                <p>{item['description']}</p>
                <p><small>Source: {item['source']} - {item['date']}</small></p>
            </div>
            ''')
        
        html.append('</body></html>')
        return '\n'.join(html)
    
    def send_digest(self, subject, news_items):
        """Send email digest"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.username
        msg['To'] = self.username
        
        html_content = self.create_html_digest(news_items)
        msg.attach(MIMEText(html_content, 'html'))
        
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.username, self.password)
                server.send_message(msg)
            print('Email digest sent successfully')
        except Exception as e:
            print(f'Error sending email: {e}')
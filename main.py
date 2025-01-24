"""Daily Brief Bot main program"""
import asyncio
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import aiosmtplib
from typing import Dict, List, Any
import logging
import os
from tenacity import retry, stop_after_attempt, wait_exponential

from config import EMAIL_CONFIG, CONTENT_CONFIG, SUBSCRIBERS
from crawlers.hacker_news import HackerNewsCrawler
from crawlers.weibo import WeiboCrawler
from crawlers.xiaohongshu import XiaohongshuCrawler
from utils.content_filter import ContentFilter

# 设置更详细的日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def fetch_source_content(crawler, limit: int, source_name: str) -> List[Dict[str, Any]]:
    """Fetch content from a single source with timeout"""
    try:
        content = await asyncio.wait_for(
            asyncio.to_thread(crawler.fetch_trending, limit),
            timeout=30
        )
        return [{**item, 'source': source_name} for item in content]
    except asyncio.TimeoutError:
        logger.error(f"Timeout fetching from {source_name}")
        return []
    except Exception as e:
        logger.error(f"Error fetching from {source_name}: {str(e)}")
        return []

async def fetch_all_content() -> Dict[str, List[Dict[str, Any]]]:
    """Fetch content from all sources in parallel"""
    sources = {
        'hacker_news': (HackerNewsCrawler(), CONTENT_CONFIG['HACKER_NEWS_LIMIT']),
        'weibo': (WeiboCrawler(), CONTENT_CONFIG['WEIBO_LIMIT']),
    }
    
    tasks = [
        fetch_source_content(crawler, limit, source)
        for source, (crawler, limit) in sources.items()
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        source: content
        for source, content in zip(sources.keys(), results)
        if isinstance(content, list)
    }

def format_email_content(content: List[Dict[str, Any]]) -> tuple[str, str]:
    """Format content into plain text and HTML email bodies"""
    date = datetime.now().strftime('%Y-%m-%d')
    
    # Plain text version
    text = f"Daily Brief - {date}\n\n"
    
    # HTML version
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: auto; }}
            .item {{ margin-bottom: 20px; padding: 10px; border-bottom: 1px solid #eee; }}
            .value {{ color: #666; font-style: italic; }}
        </style>
    </head>
    <body>
        <h1>Daily Brief - {date}</h1>
    """
    
    for item in content:
        # Plain text formatting
        text += f"\n• {item['title']}\n"
        text += f"  Source: {item['source']}\n"
        text += f"  {item.get('url', '')}\n"
        if 'value_summary' in item:
            text += f"  Value: {item['value_summary']}\n"
            
        # HTML formatting
        html += f"""
        <div class="item">
            <h3>{item['title']}</h3>
            <p><strong>Source:</strong> {item['source']}</p>
            {'<p><a href="' + item['url'] + '">' + item['url'] + '</a></p>' if item.get('url') else ''}
            {'<p class="value">' + item['value_summary'] + '</p>' if 'value_summary' in item else ''}
        </div>
        """
    
    html += "</body></html>"
    return text, html

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def send_email_async(subscriber: str, text_content: str, html_content: str):
    """Send email using aiosmtplib"""
    try:
        # 打印邮件配置信息（注意不要打印密码）
        logger.info(f"Email Configuration:")
        logger.info(f"SMTP Server: {EMAIL_CONFIG['SMTP_SERVER']}")
        logger.info(f"SMTP Port: {EMAIL_CONFIG['SMTP_PORT']}")
        logger.info(f"Sender Email: {EMAIL_CONFIG['SENDER_EMAIL']}")
        logger.info(f"Recipient: {subscriber}")
        
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_CONFIG['SENDER_EMAIL']
        msg['To'] = subscriber
        msg['Subject'] = f"Daily Brief - {datetime.now().strftime('%Y-%m-%d')}"
        
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        logger.info("Connecting to SMTP server...")
        server = aiosmtplib.SMTP(
            hostname=EMAIL_CONFIG['SMTP_SERVER'],
            port=EMAIL_CONFIG['SMTP_PORT'],
            use_tls=True
        )
        
        logger.info("Establishing connection...")
        await server.connect()
        
        logger.info("Attempting login...")
        await server.login(
            EMAIL_CONFIG['SENDER_EMAIL'],
            EMAIL_CONFIG['SENDER_PASSWORD']
        )
        
        logger.info("Sending message...")
        await server.send_message(msg)
        
        logger.info("Closing connection...")
        await server.quit()
        
        logger.info(f"Email successfully sent to {subscriber}")
        
    except aiosmtplib.SMTPException as e:
        logger.error(f"SMTP Error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while sending email: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        raise

async def send_emails(text_content: str, html_content: str):
    """Send emails to all subscribers in parallel"""
    tasks = [
        send_email_async(subscriber, text_content, html_content)
        for subscriber in SUBSCRIBERS
    ]
    await asyncio.gather(*tasks, return_exceptions=True)

async def main():
    """Main program flow"""
    try:
        logger.info("Starting Daily Brief Bot")
        
        # 打印环境变量检查（注意不要打印敏感信息）
        logger.info("Checking environment variables:")
        required_vars = ['SMTP_SERVER', 'SMTP_PORT', 'SENDER_EMAIL']
        for var in required_vars:
            logger.info(f"{var} is {'set' if var in EMAIL_CONFIG else 'not set'}")
        
        # Fetch content
        content_dict = await fetch_all_content()
        if not content_dict:
            logger.error("No content fetched")
            return
            
        # Filter content
        content_filter = ContentFilter()
        filtered_content = content_filter.filter_content(content_dict)
        if not filtered_content:
            logger.error("Content filtering failed")
            return
            
        # Format email
        text_content, html_content = format_email_content(filtered_content)
        
        # Send emails
        logger.info(f"Attempting to send emails to {len(SUBSCRIBERS)} subscribers")
        await send_emails(text_content, html_content)
        logger.info("Daily brief completed successfully")
        
    except Exception as e:
        logger.error(f"Fatal error in main program: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        raise

if __name__ == "__main__":
    asyncio.run(main())

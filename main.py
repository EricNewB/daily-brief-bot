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
from tenacity import retry, stop_after_attempt, wait_exponential

from config import EMAIL_CONFIG, CONTENT_CONFIG, SUBSCRIBERS
from crawlers.hacker_news import HackerNewsCrawler
from crawlers.weibo import WeiboCrawler
from crawlers.xiaohongshu import XiaohongshuCrawler
from utils.content_filter import ContentFilter

logging.basicConfig(level=logging.INFO)
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
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_CONFIG['SENDER_EMAIL']
        msg['To'] = subscriber
        msg['Subject'] = f"Daily Brief - {datetime.now().strftime('%Y-%m-%d')}"
        
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        server = aiosmtplib.SMTP(
            hostname=EMAIL_CONFIG['SMTP_SERVER'],
            port=EMAIL_CONFIG['SMTP_PORT'],
            use_tls=True
        )
        await server.connect()
        await server.login(
            EMAIL_CONFIG['SENDER_EMAIL'],
            EMAIL_CONFIG['SENDER_PASSWORD']
        )
        await server.send_message(msg)
        await server.quit()
        logger.info(f"Email sent to {subscriber}")
        
    except Exception as e:
        logger.error(f"Failed to send email to {subscriber}: {str(e)}")
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
        await send_emails(text_content, html_content)
        logger.info("Daily brief completed successfully")
        
    except Exception as e:
        logger.error(f"Fatal error in main program: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())

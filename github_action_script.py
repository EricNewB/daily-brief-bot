"""
Daily Brief Bot - GitHub Actions Script
只包含核心功能，用于定时发送每日简报
"""
import os
import logging
from crawlers.hacker_news import HackerNewsCrawler
from crawlers.weibo import WeiboCrawler
from utils.content_filter import ContentFilterManager
from datetime import datetime
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 从环境变量获取配置
EMAIL_CONFIG = {
    'SMTP_SERVER': os.environ['SMTP_SERVER'],
    'SMTP_PORT': int(os.environ['SMTP_PORT']),
    'SENDER_EMAIL': os.environ['SENDER_EMAIL'],
    'SENDER_PASSWORD': os.environ['SENDER_PASSWORD']
}

def format_html_content(content):
    html = f"""
    <html>
        <head>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1 {{
                    color: #2c3e50;
                    font-size: 24px;
                    margin-bottom: 30px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #eee;
                }}
                .section {{
                    margin: 25px 0;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                }}
                .section-title {{
                    color: #2c3e50;
                    font-size: 20px;
                    font-weight: 600;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 1px solid #e9ecef;
                }}
                .item {{
                    margin: 15px 0;
                    padding: 15px;
                    background: white;
                    border-radius: 6px;
                    border-left: 4px solid #007bff;
                }}
                .item-title {{
                    font-weight: 600;
                    color: #007bff;
                    font-size: 16px;
                    margin-bottom: 8px;
                }}
                .item-url {{
                    font-size: 14px;
                    margin: 8px 0;
                }}
                .item-url a {{
                    color: #6c757d;
                    text-decoration: none;
                    display: inline-block;
                    max-width: 500px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                .item-url a:hover {{
                    color: #007bff;
                    text-decoration: underline;
                }}
                .item-desc {{
                    color: #495057;
                    margin-top: 8px;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <h1>每日要闻速递 - {datetime.now().strftime("%Y-%m-%d %H:%M")}</h1>
    """
    
    items = content['filtered_content']
    # 按来源分组
    grouped_items = {}
    for item in items:
        source = item.get('source', 'Other')
        if source not in grouped_items:
            grouped_items[source] = []
        grouped_items[source].append(item)
    
    # 为每个来源创建区块
    for source, items in grouped_items.items():
        source_title = "HackerNews" if source == "HackerNews" else "微博热搜" if source == "Weibo" else source
        html += f"""
            <div class="section">
                <div class="section-title">{source_title}</div>
        """
        for item in items:
            title = item.get('title', 'No Title')
            url = item.get('url', '#')
            description = item.get('description', '') or item.get('text', '')
            html += f"""
                <div class="item">
                    <div class="item-title">{title}</div>
                    <div class="item-url"><a href="{url}" title="{url}">🔗 查看原文</a></div>
                    <div class="item-desc">{description}</div>
                </div>
            """
        html += "</div>"
    
    html += """
        </body>
    </html>
    """
    return html

def send_email(content, recipient):
    try:
        context = ssl.create_default_context()
        
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_CONFIG['SENDER_EMAIL']
        msg['To'] = recipient
        msg['Subject'] = f'每日要闻速递 - {datetime.now().strftime("%Y-%m-%d")}'
        
        text_content = json.dumps(content, ensure_ascii=False, indent=2)
        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        
        html_content = format_html_content(content)
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        with smtplib.SMTP_SSL(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT'], context=context) as server:
            server.login(EMAIL_CONFIG['SENDER_EMAIL'], EMAIL_CONFIG['SENDER_PASSWORD'])
            server.send_message(msg)
        
        return True, "Email sent successfully"
        
    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def main():
    try:
        logger.info("开始执行每日简报任务...")
        
        # 1. 收集内容
        logger.info("开始收集内容...")
        raw_content = {
            'hackernews': HackerNewsCrawler().fetch_trending(5),
            'weibo': WeiboCrawler().fetch_trending(5)
        }
        
        # 2. AI 筛选
        logger.info("开始 AI 内容筛选...")
        content_filter = ContentFilterManager()
        filtered_content = content_filter.filter_content(raw_content)
        
        if not filtered_content:
            logger.warning("AI 筛选后没有保留任何内容")
            return
        
        # 3. 发送邮件
        logger.info(f"开始发送邮件，共 {len(filtered_content)} 条内容...")
        success, message = send_email(
            {'filtered_content': filtered_content},
            EMAIL_CONFIG['SENDER_EMAIL']  # 在实际使用时替换为你的目标邮箱
        )
        
        if success:
            logger.info("每日简报发送成功")
        else:
            logger.error(f"每日简报发送失败: {message}")
            
    except Exception as e:
        logger.error(f"任务执行失败: {str(e)}\n{traceback.format_exc()}")
        raise

if __name__ == '__main__':
    main() 
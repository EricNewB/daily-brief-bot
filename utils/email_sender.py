"""
Email sending utilities for Daily Brief Bot
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from datetime import datetime
import logging
from config import EMAIL_CONFIG, SUBSCRIBERS
from .content_filter import ContentFilterManager  # 更新导入
from flask import render_template_string

logger = logging.getLogger(__name__)

EMAIL_HOST = EMAIL_CONFIG['SMTP_SERVER']
EMAIL_PORT = EMAIL_CONFIG['SMTP_PORT']
EMAIL_HOST_USER = EMAIL_CONFIG['SENDER_EMAIL']
EMAIL_HOST_PASSWORD = EMAIL_CONFIG['SENDER_PASSWORD']
RECIPIENT = SUBSCRIBERS[0]

def format_html_content(content):
    """Format content into HTML email template"""
    content_filter = ContentFilterManager()
    
    # 获取筛选和分类后的内容
    filtered_items = content_filter.filter_content(content)
    categorized_items = content_filter.categorize_content(filtered_items)
    
    # 添加调试日志
    logger.info("分类结果:")
    for cat, items in categorized_items.items():
        logger.info(f"{cat}: {len(items)} 条内容")
        for item in items:
            logger.info(f"  - {item.get('title', 'No title')} ({item.get('source', 'Unknown')})")
    
    template_vars = {
        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'sections': {
            cat: {
                'name': info['name'],
                'items': categorized_items[cat]
            }
            for cat, info in content_filter.categories.items()
        }
    }
    
    # 读取并渲染模板
    try:
        with open('templates/email_style.html', 'r', encoding='utf-8') as f:
            template = f.read()
        return render_template_string(template, **template_vars)
    except Exception as e:
        logger.error(f"模板渲染失败: {str(e)}")
        logger.error(f"模板变量: {json.dumps(template_vars, ensure_ascii=False, default=str)}")
        return render_fallback_template(template_vars)

def render_fallback_template(vars):
    """备用的简单模板"""
    html = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: auto; padding: 20px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #eee; }}
                .item {{ margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h1>每日要闻速递 - {vars['date']}</h1>
    """
    
    for section_id, section in vars['sections'].items():
        html += f"""
            <div class="section">
                <h2>{section['name']}</h2>
        """
        
        if section['items']:
            for item in section['items']:
                title = item.get('title', 'No Title')
                url = item.get('url', '#')
                desc = item.get('description', '') or item.get('text', '')
                source = item.get('source', 'Unknown')
                
                html += f"""
                    <div class="item">
                        <h3><a href="{url}">{title}</a></h3>
                        <p>{desc}</p>
                        <p><small>来源: {source}</small></p>
                    </div>
                """
        else:
            html += "<p>暂无内容</p>"
            
        html += "</div>"
    
    html += """
        </body>
    </html>
    """
    return html

def is_english(text):
    """判断文本是否为英文"""
    import re
    # 如果文本包含超过50%的英文字符，则认为是英文
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    return english_chars > len(text) * 0.5

def translate_title(title):
    """翻译标题（使用 Claude API）"""
    content_filter = ContentFilterManager()
    try:
        translation = content_filter.translate_text(title)
        return f"🔍 {translation}"
    except Exception as e:
        logger.error(f"翻译失败: {str(e)}")
        return ""

def generate_comment(item):
    """生成评语（使用 Claude API）"""
    content_filter = ContentFilterManager()
    try:
        source = item.get('source', '')
        title = item.get('title', '')
        description = item.get('description', '') or item.get('text', '')
        
        # 根据来源和内容生成不同风格的评语
        if source == 'HackerNews':
            prompt = f"请用一句简短犀利的话评价这个科技新闻：{title}"
        elif source == 'Weibo':
            prompt = f"请用一句简短犀利的话评价这条微博热搜：{title}"
        else:
            prompt = f"请用一句简短犀利的话评价这条新闻：{title}"
            
        comment = content_filter.generate_comment(prompt)
        return f"💭 {comment}"
    except Exception as e:
        logger.error(f"生成评语失败: {str(e)}")
        return ""

def send_email(content):
    """Send email with both text and HTML content to all subscribers"""
    success_count = 0
    error_messages = []
    
    for recipient in SUBSCRIBERS:
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            msg = MIMEMultipart('alternative')
            msg['From'] = EMAIL_HOST_USER
            msg['To'] = recipient
            msg['Subject'] = f'Daily Brief - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
            
            text_content = json.dumps(content, ensure_ascii=False, indent=2)
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            
            html_content = format_html_content(content)
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, context=context) as server:
                server.login(str(EMAIL_HOST_USER), str(EMAIL_HOST_PASSWORD))
                server.send_message(msg)
            
            success_count += 1
            logger.info(f"成功发送邮件到 {recipient}")
            
        except Exception as e:
            error_msg = f"发送邮件到 {recipient} 失败: {str(e)}"
            logger.error(error_msg)
            error_messages.append(error_msg)
    
    if success_count == len(SUBSCRIBERS):
        return True, f"成功发送邮件给所有 {success_count} 个订阅者"
    elif success_count > 0:
        return True, f"部分发送成功：{success_count}/{len(SUBSCRIBERS)} 个订阅者收到邮件。错误：{'; '.join(error_messages)}"
    else:
        return False, f"发送失败：{'; '.join(error_messages)}"
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

logger = logging.getLogger(__name__)

EMAIL_HOST = EMAIL_CONFIG['SMTP_SERVER']
EMAIL_PORT = EMAIL_CONFIG['SMTP_PORT']
EMAIL_HOST_USER = EMAIL_CONFIG['SENDER_EMAIL']
EMAIL_HOST_PASSWORD = EMAIL_CONFIG['SENDER_PASSWORD']
RECIPIENT = SUBSCRIBERS[0]

def format_html_content(content):
    """Format content into HTML email template"""
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
                    display: flex;
                    gap: 15px;
                }}
                .item-content {{
                    flex: 1;
                }}
                .item-image {{
                    width: 120px;
                    height: 80px;
                    border-radius: 4px;
                    overflow: hidden;
                    flex-shrink: 0;
                }}
                .item-image img {{
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }}
                .item-title {{
                    font-weight: 600;
                    color: #007bff;
                    font-size: 16px;
                    margin-bottom: 4px;
                    text-decoration: none;
                }}
                .item-title:hover {{
                    text-decoration: underline;
                }}
                .item-translation {{
                    color: #666;
                    font-size: 14px;
                    margin-bottom: 8px;
                }}
                .item-desc {{
                    color: #495057;
                    margin: 8px 0;
                    font-size: 14px;
                }}
                .item-meta {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-top: 8px;
                }}
                .source-tag {{
                    display: inline-block;
                    padding: 2px 6px;
                    background: #e9ecef;
                    border-radius: 4px;
                    font-size: 12px;
                    color: #6c757d;
                }}
                .item-comment {{
                    font-size: 13px;
                    color: #666;
                    margin-left: 8px;
                    font-style: italic;
                }}
            </style>
        </head>
        <body>
            <h1>每日要闻速递 - {datetime.now().strftime("%Y-%m-%d %H:%M")}</h1>
    """
    
    # 处理筛选后的内容
    if 'filtered_content' in content:
        items = content['filtered_content']
        # 按板块分组
        from app import load_section_scores  # 避免循环导入
        section_scores = load_section_scores()
        grouped_items = {
            'academic': [],
            'international_news': [],
            'gaming': [],
            'china_news': []
        }
        
        # 定义各板块的关键词
        keywords = {
            'academic': [
                'research', 'study', 'paper', 'science', 'technology', 'ai', 'ml', 'deep learning',
                'artificial intelligence', 'algorithm', 'design', 'ux', 'ui', 'hci', 'human computer',
                'interaction', 'interface', 'animation', 'computer graphics', 'visualization',
                'neural', 'machine learning', 'data science', 'computer vision', 'robotics',
                'programming', 'software', 'developer', 'code', 'tech'  # 添加更多技术相关词
            ],
            'gaming': [
                'game', 'steam', 'epic', 'gaming', 'playstation', 'xbox', 'nintendo',
                'console', 'dlc', 'gameplay', 'rpg', 'fps', 'mmorpg', 'esports',
                'release', 'update', 'patch', 'mod', 'multiplayer', 'sale', 'discount',
                'gaming', 'gamer', 'games'  # 添加更多游戏相关词
            ],
            'international_news': [
                'korea', 'usa', 'us', 'america', 'china', 'japan', 'europe', 'russia',
                'policy', 'economy', 'market', 'trade', 'politics', 'government',
                'international', 'global', 'world', 'foreign', 'diplomacy'
            ]
        }
        
        # 根据内容特征分类到不同板块
        for item in items:
            title = item.get('title', '').lower()
            desc = item.get('description', '').lower() or item.get('text', '').lower()
            source = item.get('source', '')
            content_text = f"{title} {desc}"
            
            # 首先检查是否是微博内容（优先归类为国内新闻）
            if source == 'Weibo':
                grouped_items['china_news'].append(item)
                continue
            
            # 然后按优先级检查各个板块的关键词
            categorized = False
            
            # 1. 首先检查学术板块（优先级最高）
            if any(keyword in content_text for keyword in keywords['academic']):
                grouped_items['academic'].append(item)
                categorized = True
                continue
            
            # 2. 然后检查游戏板块
            if any(keyword in content_text for keyword in keywords['gaming']):
                grouped_items['gaming'].append(item)
                categorized = True
                continue
            
            # 3. 最后检查国际新闻
            if any(keyword in content_text for keyword in keywords['international_news']):
                grouped_items['international_news'].append(item)
                categorized = True
                continue
            
            # 如果都不匹配，根据来源分配
            if not categorized:
                if source == 'HackerNews':
                    # HackerNews 的技术相关内容归为学术板块
                    if any(tech_word in content_text for tech_word in ['programming', 'software', 'developer', 'code', 'tech']):
                        grouped_items['academic'].append(item)
                    else:
                        grouped_items['international_news'].append(item)
                else:
                    grouped_items['international_news'].append(item)
        
        # 按板块生成 HTML
        for section_key, items in grouped_items.items():
            if items:  # 只显示有内容的板块
                section_info = section_scores.get(section_key, {})
                section_name = section_info.get('name', section_key)
                html += f"""
                    <div class="section">
                        <div class="section-title">{section_name}</div>
                """
                for item in items:
                    title = item.get('title', 'No Title')
                    url = item.get('url', '#')
                    description = item.get('description', '') or item.get('text', '')
                    source = item.get('source', 'Unknown')
                    image_url = item.get('image_url', '')  # 获取缩略图URL
                    
                    # 生成评语
                    comment = generate_comment(item)
                    
                    # 如果是英文标题，添加翻译
                    title_translation = ''
                    if is_english(title):
                        title_translation = translate_title(title)
                    
                    html += f"""
                        <div class="item">
                            <div class="item-content">
                                <a href="{url}" class="item-title" target="_blank">{title}</a>
                    """
                    
                    # 如果有翻译，显示翻译
                    if title_translation:
                        html += f"""
                                <div class="item-translation">{title_translation}</div>
                        """
                    
                    html += f"""
                                <div class="item-desc">{description}</div>
                                <div class="item-meta">
                                    <div class="meta-left">
                                        <span class="source-tag">{source}</span>
                                        <span class="item-comment">💭 {comment}</span>
                                    </div>
                                    <div class="meta-right">
                                        <!-- 这里会通过 JavaScript 添加反馈按钮 -->
                                    </div>
                                </div>
                            </div>
                        </div>
                    """
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
    from utils.content_filter import ContentFilter
    content_filter = ContentFilter()
    try:
        translation = content_filter.translate_text(title)
        return f"🔍 {translation}"
    except Exception as e:
        logger.error(f"翻译失败: {str(e)}")
        return ""

def generate_comment(item):
    """生成评语（使用 Claude API）"""
    from utils.content_filter import ContentFilter
    content_filter = ContentFilter()
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
            msg['Subject'] = f'Daily Brief - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            
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
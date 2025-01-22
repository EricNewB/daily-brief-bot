"""
Flask application for Daily Brief Bot testing interface
"""
from flask import Flask, render_template, jsonify, request
from utils.content_filter import ContentFilter
from crawlers.hacker_news import HackerNewsCrawler
from crawlers.weibo import WeiboCrawler
# WeChat crawler removed
from datetime import datetime
import sys
from io import StringIO
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import json
from config import EMAIL_CONFIG, SUBSCRIBERS
import traceback
from flask_apscheduler import APScheduler
from pytz import timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
content_filter = ContentFilter()
scheduler = APScheduler()

EMAIL_HOST = EMAIL_CONFIG['SMTP_SERVER']
EMAIL_PORT = EMAIL_CONFIG['SMTP_PORT']
EMAIL_HOST_USER = EMAIL_CONFIG['SENDER_EMAIL']
EMAIL_HOST_PASSWORD = EMAIL_CONFIG['SENDER_PASSWORD']
RECIPIENT = SUBSCRIBERS[0]

def capture_output():
    buffer = StringIO()
    sys.stdout = buffer
    return buffer

def restore_output(buffer):
    sys.stdout = sys.__stdout__
    return buffer.getvalue()

def fetch_hackernews():
    crawler = HackerNewsCrawler()
    return crawler.fetch_trending(5)

def fetch_weibo():
    crawler = WeiboCrawler()
    return crawler.fetch_trending(5)

# WeChat source removed

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
    
    # 处理筛选后的内容
    if 'filtered_content' in content:
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
    else:
        # 处理原始内容格式
        for source, items in content.items():
            source_title = "HackerNews" if source == "hackernews" else "微博热搜" if source == "weibo" else source
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

def send_test_email(content):
    try:
        context = ssl.create_default_context()
        # 在开发环境中禁用证书验证（不推荐在生产环境中使用）
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_HOST_USER
        msg['To'] = RECIPIENT
        msg['Subject'] = f'Daily Brief Test - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        text_content = json.dumps(content, ensure_ascii=False, indent=2)
        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        
        html_content = format_html_content(content)
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, context=context) as server:
            server.login(str(EMAIL_HOST_USER), str(EMAIL_HOST_PASSWORD))
            server.send_message(msg)
        
        return True, "Email sent successfully"
        
    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def send_daily_brief():
    """每日自动发送邮件的任务"""
    logger.info("开始执行每日简报任务...")
    try:
        # 1. 收集所有来源的内容
        raw_content = {
            'hackernews': fetch_hackernews(),
            'weibo': fetch_weibo()
        }
        
        # 2. 使用 AI 进行内容筛选
        logger.info("开始 AI 内容筛选...")
        filtered_content = content_filter.filter_content(raw_content)
        
        if not filtered_content:
            logger.warning("AI 筛选后没有保留任何内容")
            return
        
        # 3. 发送筛选后的内容
        logger.info(f"发送筛选后的 {len(filtered_content)} 条内容...")
        success, message = send_test_email({'filtered_content': filtered_content})
        
        if success:
            logger.info("每日简报发送成功")
        else:
            logger.error(f"每日简报发送失败: {message}")
            
    except Exception as e:
        logger.error(f"每日简报任务执行失败: {str(e)}\n{traceback.format_exc()}")

# 配置定时任务
def init_scheduler():
    """初始化定时任务"""
    # 设置时区为中国时区
    scheduler.timezone = timezone('Asia/Shanghai')
    
    # 添加定时任务，每天早上 9 点发送
    scheduler.add_job(
        id='daily_brief_job',
        func=send_daily_brief,
        trigger='cron',
        hour=9,
        minute=0,
        misfire_grace_time=3600  # 如果错过执行时间，允许在一小时内补发
    )
    
    scheduler.start()
    logger.info("定时任务已启动，将在每天早上 9 点发送每日简报")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test/hacker-news')
def test_hackernews():
    buffer = capture_output()
    try:
        results = fetch_hackernews()
        output = restore_output(buffer)
        return jsonify({'success': True, 'data': results, 'log': output})
    except Exception as e:
        output = restore_output(buffer)
        return jsonify({'success': False, 'error': str(e), 'log': output})

@app.route('/test/weibo')
def test_weibo():
    buffer = capture_output()
    try:
        results = fetch_weibo()
        output = restore_output(buffer)
        return jsonify({'success': True, 'data': results, 'log': output})
    except Exception as e:
        output = restore_output(buffer)
        return jsonify({'success': False, 'error': str(e), 'log': output})

@app.route('/test/all')
def test_all():
    buffer = capture_output()
    try:
        results = {
            'hacker-news': fetch_hackernews(),
            'weibo': fetch_weibo(),
            # WeChat source removed
        }
        output = restore_output(buffer)
        return jsonify({'success': True, 'data': results, 'log': output})
    except Exception as e:
        output = restore_output(buffer)
        return jsonify({'success': False, 'error': str(e), 'log': output})

@app.route('/test/email')
def test_email():
    buffer = capture_output()
    try:
        # 1. 收集所有来源的内容
        raw_content = {
            'hackernews': fetch_hackernews(),
            'weibo': fetch_weibo()
        }
        
        # 2. 使用 AI 进行内容筛选
        logger.info("开始 AI 内容筛选...")
        filtered_content = content_filter.filter_content(raw_content)
        
        if not filtered_content:
            logger.warning("AI 筛选后没有保留任何内容")
            output = restore_output(buffer)
            return jsonify({
                'success': False,
                'error': '内容筛选后为空',
                'log': output
            })
        
        # 3. 发送筛选后的内容
        logger.info(f"发送筛选后的 {len(filtered_content)} 条内容...")
        success, message = send_test_email({'filtered_content': filtered_content})
        
        output = restore_output(buffer)
        return jsonify({
            'success': success,
            'message': message,
            'log': output,
            'debug': {
                'raw_content_count': sum(len(items) for items in raw_content.values()),
                'filtered_content_count': len(filtered_content)
            }
        })
        
    except Exception as e:
        output = restore_output(buffer)
        return jsonify({
            'success': False,
            'error': str(e),
            'log': output
        })

@app.route('/filter', methods=['POST'])
def filter_content():
    try:
        content = request.json.get('content')
        if not content:
            return jsonify({'success': False, 'error': 'No content provided'})

        # 添加详细调试信息
        debug_info = {
            'input_sources': list(content.keys()),
            'source_counts': {k: len(v) for k, v in content.items()},
            'total_items': sum(len(v) for v in content.values())
        }
        
        logger.info(f"收到筛选请求，内容统计: {debug_info}")
        
        # 确保内容格式正确
        if not isinstance(content, dict):
            logger.error(f"内容格式错误: 期望 dict，实际是 {type(content)}")
            return jsonify({'success': False, 'error': 'Invalid content format'})
            
        # 验证每个来源的内容
        for source, items in content.items():
            if not isinstance(items, list):
                logger.error(f"来源 {source} 的内容格式错误: 期望 list，实际是 {type(items)}")
                return jsonify({'success': False, 'error': f'Invalid content format for source {source}'})
            
            # 验证每个项目的必要字段
            for item in items:
                if not isinstance(item, dict):
                    logger.error(f"来源 {source} 的项目格式错误: 期望 dict，实际是 {type(item)}")
                    continue
                if not all(k in item for k in ['title', 'url', 'source']):
                    logger.error(f"来源 {source} 的项目缺少必要字段: {item}")
                    continue

        # 调用内容过滤器
        try:
            filtered_content = content_filter.filter_content(content)
            
            if not filtered_content:
                logger.warning("内容过滤器返回空结果")
                return jsonify({
                    'success': True, 
                    'data': [],
                    'debug': {**debug_info, 'filter_result': 'empty'}
                })
                
            logger.info(f"筛选完成，保留 {len(filtered_content)} 条内容")
            return jsonify({
                'success': True, 
                'data': filtered_content,
                'debug': {**debug_info, 'filter_result': 'success', 'filtered_count': len(filtered_content)}
            })
            
        except Exception as e:
            logger.error(f"内容过滤失败: {str(e)}\n{traceback.format_exc()}")
            return jsonify({
                'success': False, 
                'error': f'Content filtering failed: {str(e)}',
                'debug': {**debug_info, 'filter_error': str(e)}
            })

    except Exception as e:
        logger.error(f'Content filtering failed: {str(e)}\n{traceback.format_exc()}')
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    init_scheduler()  # 启动定时任务
    app.run(host='0.0.0.0', port=5001, debug=True)
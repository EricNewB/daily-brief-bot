"""
Flask application for Daily Brief Bot testing interface
"""
from flask import Flask, render_template, jsonify, request, redirect, url_for
from utils.content_filter import ContentFilterManager
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
from config import EMAIL_CONFIG, SUBSCRIBERS, USER_INTERESTS
import traceback
from flask_apscheduler import APScheduler
from pytz import timezone
import os
from utils.email_sender import send_email
import requests
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
content_filter = ContentFilterManager()
scheduler = APScheduler()

EMAIL_HOST = EMAIL_CONFIG['SMTP_SERVER']
EMAIL_PORT = EMAIL_CONFIG['SMTP_PORT']
EMAIL_HOST_USER = EMAIL_CONFIG['SENDER_EMAIL']
EMAIL_HOST_PASSWORD = EMAIL_CONFIG['SENDER_PASSWORD']
RECIPIENT = SUBSCRIBERS[0]

# 存储最后一次推送的内容
last_push_content = None

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
                .source-tag {{
                    display: inline-block;
                    padding: 2px 6px;
                    background: #e9ecef;
                    border-radius: 4px;
                    font-size: 12px;
                    color: #6c757d;
                    margin-left: 8px;
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
        section_scores = load_section_scores()
        grouped_items = {
            'academic': [],
            'gaming': [],
            'international_news': [],
            'china_news': [],
            'bilibili': []  # 新增 bilibili 板块
        }
        
        # 根据内容特征分类到不同板块
        for item in items:
            title = item.get('title', '').lower()
            desc = item.get('description', '').lower()
            source = item.get('source', '')
            
            # bilibili 内容
            if source == 'Bilibili':
                grouped_items['bilibili'].append(item)
            # 学术板块
            elif any(keyword in title.lower() or keyword in desc.lower() 
                  for keyword in ['research', 'study', 'paper', 'science', 'ai', 'algorithm', 'design', 'analysis']):
                grouped_items['academic'].append(item)
            # 游戏资讯
            elif any(keyword in title.lower() or keyword in desc.lower() 
                    for keyword in ['game', 'gaming', 'steam', 'epic', 'playstation', 'xbox', 'nintendo']):
                grouped_items['gaming'].append(item)
            # 国际新闻
            elif any(country in title.lower() or country in desc.lower() 
                    for country in ['us', 'usa', 'america', 'europe', 'japan', 'korea', 'russia', 'uk']):
                grouped_items['international_news'].append(item)
            # 国内热点（默认微博内容归为国内热点）
            elif source == 'Weibo' or '中国' in title or '国内' in title:
                grouped_items['china_news'].append(item)
            # 其他内容根据来源分配
            else:
                if source == 'HackerNews':
                    grouped_items['international_news'].append(item)
                else:
                    grouped_items['china_news'].append(item)
        
        # 按板块生成 HTML，确保所有板块都显示
        for section_key in grouped_items.keys():
            section_info = section_scores.get(section_key, {
                'name': '学术论文' if section_key == 'academic' else
                      '游戏资讯' if section_key == 'gaming' else
                      '国际新闻' if section_key == 'international_news' else
                      '国内热点' if section_key == 'china_news' else
                      'UP主更新' if section_key == 'bilibili' else section_key,
                'score': 5,
                'description': '暂无描述'
            })
            section_name = section_info.get('name', section_key)
            items = grouped_items[section_key]
            
            html += f"""
                <div class="section">
                    <div class="section-title">{section_name}</div>
            """
            
            if items:
                for item in items:
                    title = item.get('title', 'No Title')
                    url = item.get('url', '#')
                    description = item.get('description', '') or item.get('text', '')
                    source = item.get('source', 'Unknown')
                    up_name = item.get('up_name', '') if source == 'Bilibili' else ''
                    
                    html += f"""
                        <div class="item" data-source="{section_key}">
                            <div class="item-title">
                                {title}
                                <span class="source-tag">{source}</span>
                                {f'<span class="up-name">UP: {up_name}</span>' if up_name else ''}
                            </div>
                            <div class="item-url"><a href="{url}" title="{url}">🔗 查看原文</a></div>
                            <div class="item-desc">{description}</div>
                            <div class="item-meta">
                                <div class="meta-left"></div>
                                <div class="meta-right"></div>
                            </div>
                        </div>
                    """
            else:
                html += f"""
                    <div class="item" style="text-align: center; color: #666;">
                        暂无{section_name}相关内容
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

# 统一的邮件发送逻辑
def send_daily_brief(is_test=False):
    """统一的邮件发送逻辑，用于定时任务和测试"""
    global last_push_content
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
            return False, "内容筛选后为空"
        
        # 3. 发送筛选后的内容
        logger.info(f"发送筛选后的 {len(filtered_content)} 条内容...")
        content_data = {'filtered_content': filtered_content}
        success, message = send_email(content_data)
        
        if success:
            # 保存最后一次推送的内容
            last_push_content = format_html_content(content_data)
            logger.info("邮件发送成功")
            return True, "邮件发送成功"
        else:
            logger.error(f"邮件发送失败: {message}")
            return False, f"邮件发送失败: {message}"
            
    except Exception as e:
        error_msg = f"执行失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return False, error_msg

# 配置定时任务
def init_scheduler():
    """初始化定时任务"""
    scheduler.timezone = timezone('Asia/Shanghai')
    scheduler.add_job(
        id='daily_brief_job',
        func=send_daily_brief,
        trigger='cron',
        hour=9,
        minute=0,
        misfire_grace_time=3600
    )
    scheduler.start()
    logger.info("定时任务已启动，将在每天早上 9 点发送每日简报")

@app.route('/')
def index():
    """主页重定向到测试面板"""
    return redirect(url_for('test_panel'))

@app.route('/test_panel')
def test_panel():
    """开发测试面板"""
    return render_template('test_panel.html')

@app.route('/optimize')
def optimize():
    section_scores = load_section_scores()
    return render_template('optimize.html', section_scores=section_scores)

@app.route('/update_score', methods=['POST'])
def update_score():
    """手机端优化后的测试"""
    section = request.form.get('section')
    section_scores = load_section_scores()
    
    if section in section_scores:
        # 降低选中板块的分数
        section_scores[section]['score'] = max(1, section_scores[section]['score'] - 1)
        save_section_scores(section_scores)
        
        # 根据分数调整 USER_INTERESTS 中的配置
        adjust_interests_by_score(section, section_scores[section]['score'])
        
        # 发送测试邮件
        try:
            success, message = send_daily_brief(is_test=True)
            if success:
                return jsonify({
                    'success': True,
                    'message': f'已优化 {section_scores[section]["name"]} 板块，并发送测试邮件到您的邮箱',
                    'new_score': section_scores[section]['score']
                })
            else:
                return jsonify({
                    'success': True,
                    'message': f'已优化 {section_scores[section]["name"]} 板块（{message}）',
                    'new_score': section_scores[section]['score']
                })
        except Exception as e:
            logger.error(f"发送测试邮件失败: {str(e)}")
            return jsonify({
                'success': True,
                'message': f'已优化 {section_scores[section]["name"]} 板块（发送测试邮件失败：{str(e)}）',
                'new_score': section_scores[section]['score']
            })
    
    return jsonify({'success': False, 'message': '未找到指定板块'})

def adjust_interests_by_score(section, score):
    """根据分数调整板块的搜索配置"""
    if section not in USER_INTERESTS:
        return
    
    section_config = USER_INTERESTS[section]
    
    # 根据分数调整配置
    if score <= 2:  # 分数很低，大幅调整
        if 'limit' in section_config:
            section_config['limit'] = max(1, section_config['limit'] - 1)
        if 'min_popularity' in section_config:
            section_config['min_popularity'] *= 1.5  # 提高热度阈值
    elif score <= 5:  # 分数中等，适度调整
        if 'min_popularity' in section_config:
            section_config['min_popularity'] *= 1.2
    # 分数较高时保持原样

@app.route('/edit_sections')
def edit_sections():
    """编辑板块页面（预留）"""
    section_scores = load_section_scores()
    return render_template('edit_sections.html', section_scores=section_scores)

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
    """测试邮件发送"""
    buffer = capture_output()
    try:
        # 获取所有来源的内容
        content = {}
        
        # 获取HackerNews内容
        hn_content = fetch_hackernews()
        if hn_content:
            content['HackerNews'] = hn_content
            
        # 获取微博内容
        weibo_content = fetch_weibo()
        if weibo_content:
            content['Weibo'] = weibo_content
            
        # 获取B站内容
        bilibili_response = test_bilibili()
        if isinstance(bilibili_response, dict) and bilibili_response.get('success'):
            content['Bilibili'] = bilibili_response.get('data', [])
        
        if not content:
            raise Exception('没有获取到任何内容')
            
        # 发送邮件
        success, message = send_email(content)
        
        output = restore_output(buffer)
        return jsonify({
            'success': success,
            'message': message,
            'log': output
        })
            
    except Exception as e:
        output = restore_output(buffer)
        return jsonify({
            'success': False,
            'message': f'邮件发送失败: {str(e)}',
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

# 加载板块评分
def load_section_scores():
    try:
        with open('config/section_scores.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# 保存板块评分
def save_section_scores(scores):
    with open('config/section_scores.json', 'w', encoding='utf-8') as f:
        json.dump(scores, f, ensure_ascii=False, indent=4)

@app.route('/api/last_push')
def get_last_push():
    """获取最后一次推送的内容"""
    if last_push_content is None:
        return jsonify({
            'success': False,
            'message': '还没有推送过内容'
        })
    return jsonify({
        'success': True,
        'html': last_push_content
    })

@app.route('/api/feedback', methods=['POST'])
def handle_feedback():
    """处理用户反馈"""
    source = request.json.get('source')
    is_positive = request.json.get('is_positive')
    
    if not source:
        return jsonify({
            'success': False,
            'message': '未指定内容来源'
        })
    
    # 根据来源找到对应的板块
    section = None
    if source == 'HackerNews':
        section = 'international_news'  # HackerNews 内容主要归类为国际新闻
    elif source == 'Weibo':
        section = 'china_news'  # 微博内容归类为国内新闻
    
    if not section:
        return jsonify({
            'success': False,
            'message': '无法识别的内容来源'
        })
    
    # 加载当前评分
    section_scores = load_section_scores()
    if section not in section_scores:
        return jsonify({
            'success': False,
            'message': '未找到对应板块'
        })
    
    # 更新评分
    current_score = section_scores[section]['score']
    if is_positive:
        new_score = min(10, current_score + 0.5)  # 每次加0.5分
    else:
        new_score = max(1, current_score - 0.5)  # 每次减0.5分
    
    section_scores[section]['score'] = new_score
    save_section_scores(section_scores)
    
    # 根据新的评分调整内容筛选规则
    adjust_interests_by_score(section, new_score)
    
    return jsonify({
        'success': True,
        'message': f"已{'提高' if is_positive else '降低'} {section_scores[section]['name']} 的评分",
        'new_score': new_score
    })

# 加载 UP 主列表
def load_up_users():
    """加载UP主列表"""
    try:
        # 确保config目录存在
        os.makedirs('config', exist_ok=True)
        
        # 如果文件不存在，创建一个空的配置文件
        if not os.path.exists('config/up_users.json'):
            default_config = {'up_users': []}
            with open('config/up_users.json', 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=4)
            return default_config
            
        # 读取现有配置
        with open('config/up_users.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 确保数据结构正确
            if not isinstance(data, dict) or 'up_users' not in data:
                data = {'up_users': []}
            return data
    except Exception as e:
        logger.error(f"加载UP主列表失败: {str(e)}")
        return {'up_users': []}

def save_up_users(up_users):
    """保存UP主列表"""
    try:
        # 确保config目录存在
        os.makedirs('config', exist_ok=True)
        
        # 确保数据结构正确
        if not isinstance(up_users, dict) or 'up_users' not in up_users:
            up_users = {'up_users': []}
            
        with open('config/up_users.json', 'w', encoding='utf-8') as f:
            json.dump(up_users, f, ensure_ascii=False, indent=4)
            
    except Exception as e:
        logger.error(f"保存UP主列表失败: {str(e)}")
        raise

@app.route('/api/up_users', methods=['GET'])
def get_up_users():
    """获取UP主列表"""
    up_users = load_up_users()
    return jsonify(up_users)

@app.route('/api/up_users', methods=['POST'])
def add_up_user():
    """添加UP主"""
    try:
        uid = request.json.get('uid')
        logger.info(f"尝试添加UP主，UID: {uid}")
        
        if not uid:
            logger.warning("未提供UP主UID")
            return jsonify({
                'success': False,
                'message': '未提供UP主UID'
            }), 400
        
        # 确保UID是数字
        try:
            uid = str(int(uid))
        except ValueError:
            logger.warning(f"无效的UID格式: {uid}")
            return jsonify({
                'success': False,
                'message': 'UID必须是数字'
            }), 400
        
        # 调用B站API获取UP主信息
        try:
            up_info = get_bilibili_user_info(uid)
            
            # 加载现有UP主列表
            up_users = load_up_users()
            
            # 检查是否已存在
            if any(str(up['uid']) == uid for up in up_users['up_users']):
                logger.warning(f"UP主已存在: {uid}")
                return jsonify({
                    'success': False,
                    'message': '该UP主已在关注列表中'
                }), 400
            
            # 添加新UP主
            new_up = {
                'uid': uid,
                'name': up_info.get('name', ''),
                'face': up_info.get('face', ''),
                'sign': up_info.get('sign', '')
            }
            
            up_users['up_users'].append(new_up)
            logger.info(f"添加新UP主: {json.dumps(new_up, ensure_ascii=False)}")
            
            # 保存更新后的列表
            save_up_users(up_users)
            logger.info("成功保存UP主列表")
            
            return jsonify({
                'success': True,
                'message': f'成功添加UP主：{new_up["name"]}'
            })
            
        except Exception as e:
            logger.error(f"获取UP主信息失败: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'获取UP主信息失败：{str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"添加UP主失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'添加UP主失败：{str(e)}'
        }), 500

def get_bilibili_user_info(uid):
    max_retries = 3
    base_wait_time = 5  # 增加基础等待时间
    
    # 加载配置
    config = load_bilibili_config()
    if not config:
        raise Exception('未找到B站配置文件')
    
    # 构建更完整的请求头
    headers = {
        'User-Agent': config['headers']['User-Agent'],
        'Referer': f'https://space.bilibili.com/{uid}',  # 更具体的Referer
        'Cookie': f'SESSDATA={config["SESSDATA"]}',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Origin': 'https://space.bilibili.com',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }
    
    session = requests.Session()
    
    for retry in range(max_retries):
        try:
            if retry > 0:
                # 使用指数退避策略，每次重试等待时间翻倍
                wait_time = base_wait_time * (2 ** retry)
                logging.warning(f'第 {retry + 1} 次重试，等待 {wait_time} 秒...')
                time.sleep(wait_time)
            
            url = f'https://api.bilibili.com/x/space/acc/info?mid={uid}&jsonp=jsonp'
            response = session.get(url, headers=headers, timeout=10)
            data = response.json()
            
            if data['code'] == -799:  # 请求频率限制
                if retry == max_retries - 1:
                    raise Exception('请求过于频繁，请稍后再试')
                continue
                
            if data['code'] == -401:  # 非法访问
                logging.error('API访问未授权，请检查Cookie设置')
                raise Exception('未授权访问')
                
            if data['code'] == 0:  # 成功
                return data['data']
            
            # 其他错误
            error_msg = data.get('message', '未知错误')
            raise Exception(f'B站API返回错误: {error_msg}')
                
        except requests.exceptions.RequestException as e:
            if retry == max_retries - 1:
                raise Exception(f'网络请求失败: {str(e)}')
            continue
            
    raise Exception('超过最大重试次数')

@app.route('/api/up_users/<uid>', methods=['DELETE'])
def remove_up_user(uid):
    """删除UP主"""
    up_users = load_up_users()
    
    # 查找并删除指定UP主
    up_users['up_users'] = [up for up in up_users['up_users'] if up['uid'] != uid]
    save_up_users(up_users)
    
    return jsonify({
        'success': True,
        'message': '成功删除UP主'
    })

@app.route('/test/bilibili')
def test_bilibili():
    """测试B站更新"""
    buffer = capture_output()
    try:
        up_users = load_up_users()
        results = []
        
        for up in up_users['up_users']:
            # 获取UP主最新视频
            response = requests.get(f'https://api.bilibili.com/x/space/arc/search?mid={up["uid"]}&ps=5&order=pubdate')
            data = response.json()
            
            if data['code'] == 0:
                videos = data['data']['list']['vlist']
                for video in videos:
                    results.append({
                        'title': video['title'],
                        'description': video['description'],
                        'url': f'https://www.bilibili.com/video/{video["bvid"]}',
                        'source': 'Bilibili',
                        'up_name': up['name'],
                        'created': video['created']
                    })
        
        output = restore_output(buffer)
        return jsonify({
            'success': True,
            'data': sorted(results, key=lambda x: x['created'], reverse=True)[:5],
            'log': output
        })
        
    except Exception as e:
        output = restore_output(buffer)
        return jsonify({
            'success': False,
            'error': str(e),
            'log': output
        })

def load_bilibili_config():
    """加载B站配置"""
    try:
        with open('config/bilibili_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("未找到B站配置文件")
        return None

@app.route('/api/filter_mode', methods=['GET', 'POST'])
def filter_mode():
    """获取或设置筛选模式"""
    config_file = 'config/filter_config.json'
    
    # 确保配置文件存在
    if not os.path.exists(config_file):
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({'mode': 'ai'}, f)  # 默认使用AI筛选
    
    if request.method == 'POST':
        mode = request.json.get('mode')
        if mode not in ['ai', 'rule']:
            return jsonify({
                'success': False,
                'message': '无效的筛选模式'
            }), 400
            
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({'mode': mode}, f)
            
        return jsonify({
            'success': True,
            'message': f'已切换到{"AI" if mode == "ai" else "规则"}筛选模式'
        })
    
    # GET请求返回当前模式
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return jsonify({
                'success': True,
                'mode': config.get('mode', 'ai')
            })
    except FileNotFoundError:
        return jsonify({
            'success': True,
            'mode': 'ai'  # 默认模式
        })

@app.context_processor
def inject_common_variables():
    """注入所有模板都需要的公共变量"""
    # 加载默认配置
    try:
        with open('config/filter_config.json', 'r', encoding='utf-8') as f:
            filter_config = json.load(f)
    except FileNotFoundError:
        filter_config = {'mode': 'ai'}
    
    # 加载板块配置
    section_scores = {
        'academic': {'name': '学术科技'},
        'international_news': {'name': '国际新闻'},
        'gaming': {'name': '游戏资讯'},
        'china_news': {'name': '国内新闻'}
    }
    
    return dict(
        sections=section_scores,
        filter_mode=filter_config.get('mode', 'ai')
    )

if __name__ == '__main__':
    init_scheduler()  # 启动定时任务
    # 尝试不同的端口，直到找到可用的
    for port in range(5001, 5010):
        try:
            app.run(host='0.0.0.0', port=port, debug=True)
            break
        except OSError:
            continue
# Daily Brief Bot

一个智能的每日新闻简报机器人，通过邮件发送个性化的新闻摘要。

## 🌟 特性

- 📰 多源新闻聚合
  - HackerNews 热门内容
  - 微博热搜
- 🤖 智能内容筛选
  - 基于用户兴趣的内容过滤
  - AI 驱动的内容分析和总结
- 📧 自动邮件推送
  - 每日定时发送
  - 支持多个订阅者
  - 美观的 HTML 邮件模板
  - 完善的错误处理和重试机制
- ⚙️ 高度可定制
  - 可配置发送时间和时区
  - 灵活的内容过滤规则
  - 详细的日志记录

## 🚀 快速开始

### 前置要求

- Python 3.9+
- SMTP 邮箱账号（用于发送邮件）

### 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/daily-brief-bot.git
cd daily-brief-bot
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
创建 `.env` 文件并填入以下信息：
```env
SMTP_SERVER=your_smtp_server
SMTP_PORT=your_smtp_port
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_email_password
SENDER_EMAIL=your_sender_email
```

4. 配置个人偏好：
编辑 `config/preferences.json` 文件：
```json
{
    "email": "your_email@example.com",
    "schedule": {
        "time": "09:00",
        "timezone": "Asia/Shanghai"
    }
}
```

### 使用方法

#### 本地运行

```bash
python src/main.py
```

#### GitHub Actions 自动运行

本项目已配置 GitHub Actions 工作流，会在每天早上 9 点（北京时间）自动运行。

1. Fork 本仓库
2. 在仓库设置中配置以下 Secrets：
   - `SMTP_SERVER`
   - `SMTP_PORT`
   - `SMTP_USERNAME`
   - `SMTP_PASSWORD`
   - `SENDER_EMAIL`

## 📝 开发说明

### 项目结构

```
daily-brief-bot/
├── src/
│   ├── crawlers/          # 内容爬虫模块
│   │   ├── hacker_news.py # HackerNews爬虫
│   │   └── weibo.py      # 微博爬虫
│   ├── utils/            # 工具函数
│   │   └── content_filter.py # 内容过滤器
│   └── main.py          # 主程序入口
├── config/              # 配置文件
├── templates/           # 邮件模板
└── tests/              # 测试文件
```

### 测试

项目提供了一个测试面板，可以用来测试各个功能模块：

```bash
python app.py
```

访问 `http://localhost:5000` 使用测试面板。

## 📄 许可证

MIT

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 提交改动：`git commit -m 'Add some AmazingFeature'`
4. 推送分支：`git push origin feature/AmazingFeature`
5. 提交 Pull Request

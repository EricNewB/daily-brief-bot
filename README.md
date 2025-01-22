# Daily Brief Bot

每日新闻推荐系统，自动抓取、分析和推送各类新闻源的重要内容。

## 项目概述

Daily Brief Bot 是一个自动化信息聚合工具，使用AI技术从多个平台收集、筛选和整理热门内容，并通过邮件定期发送给订阅者。

## 项目结构

```
daily-brief/
├── crawlers/                # 爬虫模块
│   ├── hacker_news.py      # HackerNews 爬虫
│   ├── weibo.py            # 微博热搜爬虫
│   ├── wechat.py           # 微信公众号爬虫
│   └── xiaohongshu.py      # 小红书爬虫（开发中）
├── utils/                   # 工具模块
│   └── content_filter.py    # Claude内容筛选
├── static/                  # 静态资源
├── templates/               # 前端模板
├── tests/                   # 测试用例
├── app.py                   # Flask应用主文件
├── config.py               # 配置文件
└── main.py                 # 主程序入口
```

## 功能特性

1. 多源数据采集
   - HackerNews热门故事
   - 微博热搜话题
   - 微信公众号文章
   - 小红书内容（开发中）

2. AI智能筛选
   - 使用Claude API进行内容分析和筛选
   - 评估内容的信息价值、时效性、影响力
   - 智能推荐最有价值的内容

3. 邮件推送系统
   - 格式化的HTML邮件模板
   - 自动定时发送
   - 多订阅者支持

4. 测试管理界面
   - 实时数据预览
   - 爬虫测试功能
   - 调试日志显示

## 开发状态

### 2025-01-19 最新进展

#### 已完成功能
1. 基础爬虫实现
   - HackerNews（完成）
   - 微博热搜（完成）
   - 微信公众号（完成）
   - 添加了统一的fetch_trending接口

2. AI内容筛选
   - 集成Claude API
   - 实现内容评估和筛选
   - 优化筛选算法

3. 前端界面
   - 实现测试面板
   - 添加调试日志显示
   - 优化用户交互

#### 正在进行
1. 邮件系统优化
   - 修复SMTP认证问题
   - 改进邮件模板
   - 完善错误处理

2. 内容展示优化
   - 改进数据展示格式
   - 添加内容分类
   - 优化排序算法

#### 计划功能
1. 短期目标
   - 完善现有数据源的稳定性
   - 优化内容聚合算法
   - 改进用户界面

2. 长期目标
   - 扩展更多数据源
   - 添加用户自定义功能
   - 提供更多的内容分类选项

## 环境配置

### 基础环境
- Python 3.13
- Flask 3.0.2
- Anthropic API (最新版本)

### 安装步骤

1. 克隆项目：
```bash
git clone [项目地址]
cd daily-brief
```

2. 创建并激活虚拟环境：
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
创建.env文件并添加必要的配置：
```
ANTHROPIC_API_KEY=your_api_key
EMAIL_HOST_USER=your_email
EMAIL_HOST_PASSWORD=your_email_auth_code
```

5. 运行测试界面：
```bash
python app.py
```

## 开发注意事项
1. 所有爬虫必须实现fetch_trending方法
2. 确保代码符合Python代码规范
3. 添加适当的错误处理和日志记录
4. 定期检查数据源的可用性

## 贡献指南
1. Fork 本仓库
2. 创建新的特性分支
3. 提交你的改动
4. 发起 Pull Request

## 许可证
[待定]
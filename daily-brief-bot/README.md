# Daily Brief Bot

A personal daily briefing bot that sends customized news digest via email.

## Features

- Customized topic tracking
- Daily email digest
- Support for multiple information sources
- Powered by Brave Search API

## Setup

1. Configure GitHub Secrets:
   - BRAVE_API_KEY: Your Brave Search API key
   - EMAIL_USER: Your email address
   - EMAIL_PASSWORD: Your email SMTP authorization code

2. Configure your preferences in config/preferences.json

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python src/main.py
```

## License

MIT
import os
import sys
import unittest
from unittest.mock import Mock, patch
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.wechat import WeChatCrawler

class TestWeChatCrawler(unittest.TestCase):
    def setUp(self):
        self.crawler = WeChatCrawler()
        
    def test_proxy_startup(self):
        """测试代理服务器是否能正常启动"""
        try:
            self.crawler.start_proxy()
            self.assertTrue(self.crawler.proxy_running)
        finally:
            self.crawler.stop_proxy()
            
    def test_fetch_trending(self):
        """测试是否能获取热门文章"""
        with patch('crawlers.wechat.WeChatCrawler._extract_articles') as mock_extract:
            mock_extract.return_value = [
                {
                    'title': '测试文章',
                    'url': 'https://mp.weixin.qq.com/test',
                    'author': '测试公众号',
                    'timestamp': '2024-01-18 12:00:00'
                }
            ]
            
            articles = self.crawler.fetch_trending()
            self.assertIsInstance(articles, list)
            self.assertEqual(len(articles), 1)
            self.assertIn('title', articles[0])
            self.assertIn('url', articles[0])
            self.assertIn('author', articles[0])
            self.assertIn('timestamp', articles[0])
            
    def test_certificate_setup(self):
        """测试证书是否正确配置"""
        cert_path = os.path.expanduser('~/.mitmproxy/mitmproxy-ca-cert.pem')
        self.assertTrue(os.path.exists(cert_path), "mitmproxy证书未找到")
        
    def tearDown(self):
        if hasattr(self, 'crawler') and self.crawler.proxy_running:
            self.crawler.stop_proxy()

if __name__ == '__main__':
    unittest.main()
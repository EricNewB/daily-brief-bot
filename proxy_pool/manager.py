import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import os
from pathlib import Path
from .proxy import Proxy
import logging

logger = logging.getLogger(__name__)

class ProxyManager:
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_path = self.config_dir / 'proxy_config.json'
        self.data_path = self.config_dir / 'proxy_data.json'
        
        self.config = self._load_config()
        self.proxies: List[Proxy] = self._load_proxy_data()
        self._lock = asyncio.Lock()
        
        # 设置自动刷新任务
        self.refresh_task = None
        
    def _load_config(self) -> dict:
        """加载代理配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 默认配置
            default_config = {
                "test_url": "https://api.search.brave.com/health",
                "test_timeout": 5,
                "refresh_interval": 600,  # 10分钟
                "max_fail_count": 3,
                "proxy_sources": [
                    {
                        "name": "default",
                        "url": "https://proxy-provider.com/api/proxies",
                        "api_key": "your-api-key-here"
                    }
                ]
            }
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config

    def _load_proxy_data(self) -> List[Proxy]:
        """加载代理数据"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Proxy.from_dict(item) for item in data]
        except FileNotFoundError:
            return []

    async def _save_proxy_data(self):
        """保存代理数据"""
        async with self._lock:
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_path, 'w', encoding='utf-8') as f:
                data = [proxy.to_dict() for proxy in self.proxies]
                json.dump(data, f, indent=2, ensure_ascii=False)

    async def start(self):
        """启动代理管理器"""
        if self.refresh_task is None:
            self.refresh_task = asyncio.create_task(self._auto_refresh())
            logger.info("代理池自动刷新任务已启动")

    async def stop(self):
        """停止代理管理器"""
        if self.refresh_task:
            self.refresh_task.cancel()
            try:
                await self.refresh_task
            except asyncio.CancelledError:
                pass
            self.refresh_task = None
            logger.info("代理池自动刷新任务已停止")

    async def _auto_refresh(self):
        """自动刷新代理池"""
        while True:
            try:
                await self.refresh_proxies()
                await asyncio.sleep(self.config["refresh_interval"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"代理池刷新失败: {str(e)}")
                await asyncio.sleep(60)  # 出错后等待1分钟再试

    async def refresh_proxies(self):
        """刷新代理池"""
        logger.info("开始刷新代理池")
        async with self._lock:
            new_proxies = await self._fetch_proxies()
            valid_proxies = await self._validate_proxies(new_proxies)
            
            # 更新代理列表
            self.proxies = [p for p in self.proxies if p.is_active] + valid_proxies
            await self._save_proxy_data()
            
        logger.info(f"代理池刷新完成，当前有效代理数量: {len(self.proxies)}")

    async def _validate_proxies(self, proxies: List[Proxy]) -> List[Proxy]:
        """验证代理有效性"""
        valid_proxies = []
        test_url = self.config["test_url"]
        timeout = self.config["test_timeout"]

        for proxy in proxies:
            try:
                start_time = datetime.now()
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        test_url,
                        proxy=proxy.url,
                        timeout=timeout
                    ) as response:
                        if response.status == 200:
                            response_time = (datetime.now() - start_time).total_seconds() * 1000
                            proxy.response_time_ms = int(response_time)
                            proxy.last_checked = datetime.now()
                            proxy.fail_count = 0
                            proxy.is_active = True
                            valid_proxies.append(proxy)
                            logger.debug(f"代理验证成功: {proxy.url}")
            except Exception as e:
                logger.debug(f"代理验证失败: {proxy.url} - {str(e)}")
                continue

        return valid_proxies

    async def _fetch_proxies(self) -> List[Proxy]:
        """从配置的源获取代理列表"""
        all_proxies = []
        for source in self.config['proxy_sources']:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        source['url'],
                        headers={'Authorization': source['api_key']}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            proxies = [
                                Proxy(
                                    host=item['host'],
                                    port=item['port'],
                                    protocol=item.get('protocol', 'http'),
                                    username=item.get('username'),
                                    password=item.get('password')
                                )
                                for item in data
                            ]
                            all_proxies.extend(proxies)
                            logger.info(f"从 {source['name']} 获取到 {len(proxies)} 个代理")
            except Exception as e:
                logger.error(f"从 {source['name']} 获取代理失败: {str(e)}")

        return all_proxies

    async def get_proxy(self) -> Optional[Proxy]:
        """获取一个可用代理"""
        async with self._lock:
            valid_proxies = [p for p in self.proxies 
                           if p.is_active and p.fail_count < self.config['max_fail_count']]
            
            if not valid_proxies:
                await self.refresh_proxies()
                valid_proxies = [p for p in self.proxies 
                               if p.is_active and p.fail_count < self.config['max_fail_count']]
            
            if not valid_proxies:
                return None

            # 选择响应时间最快的代理
            proxy = min(valid_proxies, key=lambda p: p.response_time_ms or float('inf'))
            proxy.last_used = datetime.now()
            return proxy

    async def report_result(self, proxy: Proxy, success: bool, error_message: str = None):
        """报告代理使用结果"""
        async with self._lock:
            if success:
                proxy.fail_count = 0
                proxy.success_count += 1
                logger.debug(f"代理使用成功: {proxy.url}")
            else:
                proxy.fail_count += 1
                if proxy.fail_count >= self.config['max_fail_count']:
                    proxy.is_active = False
                    logger.warning(f"代理已禁用: {proxy.url} - {error_message}")
                else:
                    logger.debug(f"代理使用失败: {proxy.url} - {error_message}")
            
            await self._save_proxy_data()

    def get_stats(self) -> Dict:
        """获取代理池统计信息"""
        total_proxies = len(self.proxies)
        active_proxies = len([p for p in self.proxies if p.is_active])
        healthy_proxies = len([p for p in self.proxies 
                             if p.is_active and p.fail_count < self.config['max_fail_count']])
        
        return {
            "total_proxies": total_proxies,
            "active_proxies": active_proxies,
            "healthy_proxies": healthy_proxies,
            "average_response_time": sum(
                (p.response_time_ms or 0) for p in self.proxies if p.response_time_ms
            ) / total_proxies if total_proxies > 0 else 0
        }
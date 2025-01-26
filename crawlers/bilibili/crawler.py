"""
Bilibili Up主信息爬虫 - 使用httpx和aiohttp
"""
import httpx
import asyncio
import aiohttp
import json
import logging
from pathlib import Path
import time
import random
from typing import List, Dict, Optional
import hashlib
import os

logger = logging.getLogger(__name__)

class BilibiliCrawler:
    def __init__(self):
        self.client = httpx.Client(http2=True)
        self.base_url = "https://api.bilibili.com"
        self._last_request_time = 0
        self.min_request_interval = 3
        self.wbi_key = None
        self.wbi_key_expire = 0
        self.session = self._load_or_create_session()

    def _load_or_create_session(self) -> Dict[str, str]:
        session_file = Path(__file__).parent.parent.parent / 'config' / 'bilibili_session.json'
        try:
            if session_file.exists():
                with open(session_file, 'r') as f:
                    return json.load(f)
            session = self._generate_session()
            with open(session_file, 'w') as f:
                json.dump(session, f)
            return session
        except Exception as e:
            logger.error(f"处理会话时出错: {e}")
            return self._generate_session()

    def _generate_session(self) -> Dict[str, str]:
        return {
            'buvid': hashlib.md5(os.urandom(16)).hexdigest(),
            'SESSDATA': '',
            'bili_jct': hashlib.md5(os.urandom(16)).hexdigest()
        }

    def _ensure_request_interval(self):
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed + random.uniform(2, 5)
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    async def _get_wbi_key(self):
        if self.wbi_key and time.time() < self.wbi_key_expire:
            return self.wbi_key

        try:
            response = await self.client.get("https://api.bilibili.com/x/web-interface/nav")
            data = response.json()
            if data['code'] == 0:
                img_url = data['data']['wbi_img']['img_url']
                sub_url = data['data']['wbi_img']['sub_url']
                self.wbi_key = img_url.split('/')[-1].split('.')[0] + sub_url.split('/')[-1].split('.')[0]
                self.wbi_key_expire = time.time() + 3600
                return self.wbi_key
        except Exception as e:
            logger.error(f"获取wbi key失败: {e}")
        return None

    async def get_up_info(self, uid: str) -> Optional[Dict]:
        try:
            self._ensure_request_interval()

            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Origin': 'https://space.bilibili.com',
                    'Referer': f'https://space.bilibili.com/{uid}/',
                }

                params = {
                    'mid': uid,
                    'token': '',
                    'platform': 'web',
                    'web_location': '1550101',
                    'w_rid': hashlib.md5(f"{uid}{int(time.time())}".encode()).hexdigest(),
                }

                async with session.get(
                    f"{self.base_url}/x/space/wbi/acc/info",
                    headers=headers,
                    params=params,
                    cookies=self.session
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['code'] == 0:
                            return data
                        logger.error(f"获取UP主信息失败: {data}")
                    return None

        except Exception as e:
            logger.error(f"获取UP主信息失败: {e}")
            return None

    def get_up_info_sync(self, uid: str) -> Optional[Dict]:
        return asyncio.run(self.get_up_info(uid))

    async def get_up_videos(self, uid: str, page_size: int = 5) -> Optional[List[Dict]]:
        try:
            self._ensure_request_interval()

            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Origin': 'https://space.bilibili.com',
                    'Referer': f'https://space.bilibili.com/{uid}/',
                }

                params = {
                    'mid': uid,
                    'ps': page_size,
                    'tid': 0,
                    'special_type': '',
                    'pn': 1,
                    'keyword': '',
                    'order': 'pubdate',
                    'platform': 'web',
                    'web_location': '1550101',
                    'order_avoided': 'true',
                }

                async with session.get(
                    f"{self.base_url}/x/space/wbi/arc/search",
                    headers=headers,
                    params=params,
                    cookies=self.session
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['code'] == 0:
                            videos = data['data']['list']['vlist']
                            return [
                                {
                                    'title': video['title'],
                                    'description': video['description'],
                                    'url': f'https://www.bilibili.com/video/{video["bvid"]}',
                                    'source': 'Bilibili',
                                    'up_name': video['author'],
                                    'created': video['created'],
                                    'length': video.get('length', ''),
                                    'play': video.get('play', 0),
                                    'comment': video.get('comment', 0)
                                }
                                for video in videos
                            ]
                    return None

        except Exception as e:
            logger.error(f"获取UP主视频失败: {e}")
            return None

    def get_up_videos_sync(self, uid: str, page_size: int = 5) -> Optional[List[Dict]]:
        return asyncio.run(self.get_up_videos(uid, page_size))

    async def get_up_dynamics(self, uid: str) -> Optional[List[Dict]]:
        try:
            self._ensure_request_interval()

            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Origin': 'https://space.bilibili.com',
                    'Referer': f'https://space.bilibili.com/{uid}/',
                }

                params = {
                    'host_mid': uid,
                    'offset_dynamic_id': 0,
                    'need_top': 1,
                    'platform': 'web',
                }

                async with session.get(
                    f"{self.base_url}/x/polymer/web-dynamic/v1/feed/space",
                    headers=headers,
                    params=params,
                    cookies=self.session
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['code'] == 0:
                            items = data['data']['items'][:5]
                            return [
                                {
                                    'type': item['type'],
                                    'description': item.get('modules', {}).get('desc', {}).get('text', ''),
                                    'timestamp': item['modules']['module_author']['pub_ts'],
                                    'source': 'Bilibili动态',
                                }
                                for item in items
                            ]
                    return None

        except Exception as e:
            logger.error(f"获取UP主动态失败: {e}")
            return None

    def get_up_dynamics_sync(self, uid: str) -> Optional[List[Dict]]:
        return asyncio.run(self.get_up_dynamics(uid))

    def fetch_trending(self, limit: int = 5) -> List[Dict]:
        try:
            config_path = Path(__file__).parent.parent.parent / 'config' / 'up_users.json'
            if not config_path.exists():
                return []
            
            with open(config_path, 'r', encoding='utf-8') as f:
                up_users = json.load(f)
            
            all_updates = []
            for up in up_users.get('up_users', []):
                try:
                    uid = up['uid']
                    videos = self.get_up_videos_sync(uid)
                    if videos:
                        all_updates.extend(videos)
                    
                    dynamics = self.get_up_dynamics_sync(uid)
                    if dynamics:
                        all_updates.extend(dynamics)
                    
                    time.sleep(random.uniform(3, 6))
                except Exception as e:
                    logger.error(f"获取UP主 {uid} 的更新失败: {e}")
                    continue
            
            all_updates.sort(key=lambda x: x.get('created', 0) or x.get('timestamp', 0), reverse=True)
            return all_updates[:limit]
            
        except Exception as e:
            logger.error(f"获取UP主更新失败: {e}")
            return []
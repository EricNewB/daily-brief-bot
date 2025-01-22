from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Proxy:
    host: str
    port: int
    protocol: str = "http"
    username: Optional[str] = None
    password: Optional[str] = None
    last_used: Optional[datetime] = None
    last_checked: Optional[datetime] = None
    fail_count: int = 0
    success_count: int = 0
    response_time_ms: Optional[int] = None
    is_active: bool = True
    
    @property
    def url(self) -> str:
        """获取代理URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "username": self.username,
            "password": self.password,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "fail_count": self.fail_count,
            "success_count": self.success_count,
            "response_time_ms": self.response_time_ms,
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Proxy':
        """从字典创建代理对象"""
        if "last_used" in data and data["last_used"]:
            data["last_used"] = datetime.fromisoformat(data["last_used"])
        if "last_checked" in data and data["last_checked"]:
            data["last_checked"] = datetime.fromisoformat(data["last_checked"])
        return cls(**data)
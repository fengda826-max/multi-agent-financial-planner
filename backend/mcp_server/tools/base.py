from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime


class DataSourceAdapter(ABC):
    """数据源适配器基类"""

    def __init__(self, name: str, rate_limit: int = 10):
        self.name = name
        self.rate_limit = rate_limit
        self._request_count = 0
        self._last_reset = datetime.utcnow()

    async def check_rate_limit(self):
        """检查速率限制"""
        now = datetime.utcnow()
        if (now - self._last_reset).seconds >= 60:
            self._request_count = 0
            self._last_reset = now
        if self._request_count >= self.rate_limit:
            wait_time = 60 - (now - self._last_reset).seconds
            await asyncio.sleep(wait_time)
            self._request_count = 0
            self._last_reset = datetime.utcnow()
        self._request_count += 1

    @abstractmethod
    async def get_index_data(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_fund_rating(self, fund_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_macro_indicator(self, indicator: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_bond_yield(self, curve_type: str = "china") -> Dict[str, Any]:
        pass
